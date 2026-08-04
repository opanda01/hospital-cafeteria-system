package apiclient

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type Client struct {
	baseURL      string
	deviceKey    string
	deviceAPIKey string
	internalKey  string
	http         *http.Client
}

func New(baseURL, deviceKey, deviceAPIKey, internalKey string) *Client {
	return &Client{
		baseURL:      baseURL,
		deviceKey:    deviceKey,
		deviceAPIKey: deviceAPIKey,
		internalKey:  internalKey,
		http:         &http.Client{Timeout: 15 * time.Second},
	}
}

type SyncResponse struct {
	CacheVersion int `json:"cache_version"`
	Cards        []struct {
		KartUID string `json:"kart_uid"`
		UserID  int    `json:"user_id"`
	} `json:"cards"`
	Entitlements []struct {
		UserID    int `json:"user_id"`
		MealID    int `json:"meal_id"`
		KalanHak  int `json:"kalan_hak"`
	} `json:"entitlements"`
}

func (c *Client) Sync() (*SyncResponse, error) {
	url := fmt.Sprintf("%s/internal/edge/v1/sync?device_key=%s", c.baseURL, c.deviceKey)
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	c.setHeaders(req)
	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("sync failed: %s", string(body))
	}
	var out SyncResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, err
	}
	return &out, nil
}

type ValidateRequest struct {
	CardUID        string `json:"card_uid"`
	DeviceKey      string `json:"device_key"`
	EventID        string `json:"event_id,omitempty"`
	OfflineSenkron bool   `json:"offline_senkron"`
}

type ValidateResponse struct {
	Sonuc string `json:"sonuc"`
}

func (c *Client) ValidateAccess(cardUID, eventID string, offline bool) (*ValidateResponse, error) {
	body, _ := json.Marshal(ValidateRequest{
		CardUID:        cardUID,
		DeviceKey:      c.deviceKey,
		EventID:        eventID,
		OfflineSenkron: offline,
	})
	req, err := http.NewRequest(http.MethodPost, c.baseURL+"/access/validate", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	c.setHeaders(req)
	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		b, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("validate failed: %s", string(b))
	}
	var out ValidateResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, err
	}
	return &out, nil
}

func (c *Client) setHeaders(req *http.Request) {
	if c.deviceAPIKey != "" {
		req.Header.Set("X-Device-Api-Key", c.deviceAPIKey)
	}
	if c.internalKey != "" {
		req.Header.Set("X-Internal-Key", c.internalKey)
	}
}
