package main

import (
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/google/uuid"
	"github.com/yemekhane/edge-gateway/internal/apiclient"
	"github.com/yemekhane/edge-gateway/internal/cache"
	"github.com/yemekhane/edge-gateway/internal/config"
	"github.com/yemekhane/edge-gateway/internal/metrics"
	"github.com/yemekhane/edge-gateway/internal/mqttclient"
	"github.com/yemekhane/edge-gateway/internal/queue"
	"github.com/yemekhane/edge-gateway/internal/tcpreader"
)

func main() {
	cfg := config.Load()
	store, err := cache.Open(cfg.DataDir)
	if err != nil {
		log.Fatal(err)
	}
	defer store.Close()

	q, err := queue.Open(cfg.DataDir)
	if err != nil {
		log.Fatal(err)
	}

	api := apiclient.New(cfg.APIURL, cfg.DeviceID, cfg.DeviceAPIKey, cfg.InternalKey)
	mqtt, err := mqttclient.Connect(cfg.MQTTBroker, cfg.DeviceID, cfg.TenantID)
	if err != nil {
		log.Printf("mqtt connect failed (REST fallback): %v", err)
	}

	go func() {
		if err := metrics.Serve(cfg.MetricsAddr); err != nil {
			log.Fatal(err)
		}
	}()

	go syncLoop(cfg, api, store)
	go heartbeatLoop(cfg, mqtt, store, q)
	go flushQueueLoop(api, mqtt, q)

	err = tcpreader.Listen(cfg.TCPListen, func(cardUID string) {
		metrics.EventsTotal.Inc()
		eventID := uuid.NewString()
		ok, preliminary := store.CardAllowed(cardUID)
		payload := map[string]any{
			"event_id":         eventID,
			"tenant_id":        cfg.TenantID,
			"device_key":       cfg.DeviceID,
			"card_uid":         cardUID,
			"ts":               time.Now().UTC().Format(time.RFC3339),
			"edge_preliminary": preliminary,
		}
		if mqtt != nil && mqtt.Connected() {
			if err := mqtt.PublishEvent(payload); err != nil {
				_ = q.Push("event", payload)
				if ok {
					if _, err := api.ValidateAccess(cardUID, eventID, true); err != nil {
						_ = q.Push("validate", map[string]string{"card_uid": cardUID, "event_id": eventID})
					}
				}
			}
		} else {
			_ = q.Push("event", payload)
			if ok {
				if _, err := api.ValidateAccess(cardUID, eventID, true); err != nil {
					_ = q.Push("validate", map[string]string{"card_uid": cardUID, "event_id": eventID})
				}
			}
		}
	})
	if err != nil {
		log.Fatal(err)
	}
	select {}
}

func syncLoop(cfg config.Config, api *apiclient.Client, store *cache.Store) {
	runSync(api, store)
	ticker := time.NewTicker(time.Duration(cfg.SyncIntervalS) * time.Second)
	defer ticker.Stop()
	for range ticker.C {
		runSync(api, store)
	}
}

func runSync(api *apiclient.Client, store *cache.Store) {
	resp, err := api.Sync()
	if err != nil {
		log.Printf("sync error: %v", err)
		return
	}
	cards := map[string]int{}
	for _, c := range resp.Cards {
		cards[c.KartUID] = c.UserID
	}
	ents := map[string]int{}
	for _, e := range resp.Entitlements {
		key := fmt.Sprintf("%d:%d", e.UserID, e.MealID)
		ents[key] = e.KalanHak
	}
	_ = store.ReplaceCards(cards)
	_ = store.ReplaceEntitlements(ents)
	_ = store.SetCacheVersion(resp.CacheVersion)
	log.Printf("cache synced v%d cards=%d", resp.CacheVersion, len(cards))
}

func heartbeatLoop(cfg config.Config, mqtt *mqttclient.Client, store *cache.Store, q *queue.DiskQueue) {
	ticker := time.NewTicker(time.Duration(cfg.HeartbeatSec) * time.Second)
	defer ticker.Stop()
	for range ticker.C {
		metrics.QueueDepth.Set(float64(q.Depth()))
		if mqtt != nil {
			if mqtt.Connected() {
				metrics.MQTTConnected.Set(1)
			} else {
				metrics.MQTTConnected.Set(0)
			}
			payload := map[string]any{
				"tenant_id":     cfg.TenantID,
				"device_key":    cfg.DeviceID,
				"ts":            time.Now().UTC().Format(time.RFC3339),
				"firmware":      cfg.Firmware,
				"queue_depth":   q.Depth(),
				"cache_version": store.CacheVersion(),
			}
			_ = mqtt.PublishHeartbeat(payload)
		}
	}
}

func flushQueueLoop(api *apiclient.Client, mqtt *mqttclient.Client, q *queue.DiskQueue) {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()
	for range ticker.C {
		_ = q.Drain(func(item queue.Item) error {
			switch item.Kind {
			case "event":
				if mqtt != nil && mqtt.Connected() {
					var payload map[string]any
					if err := json.Unmarshal(item.Payload, &payload); err != nil {
						return nil
					}
					return mqtt.PublishEvent(payload)
				}
				return fmt.Errorf("mqtt down")
			case "validate":
				var p struct {
					CardUID string `json:"card_uid"`
					EventID string `json:"event_id"`
				}
				if err := json.Unmarshal(item.Payload, &p); err != nil {
					return nil
				}
				_, err := api.ValidateAccess(p.CardUID, p.EventID, true)
				return err
			}
			return nil
		})
	}
}
