package config

import (
	"os"
)

type Config struct {
	DeviceID      string
	TenantID      string
	TCPListen     string
	APIURL        string
	MQTTBroker    string
	DeviceAPIKey  string
	InternalKey   string
	MetricsAddr   string
	Firmware      string
	HeartbeatSec  int
	SyncIntervalS int
	DataDir       string
}

func Load() Config {
	return Config{
		DeviceID:      getenv("EDGE_DEVICE_ID", "reader-giris-1"),
		TenantID:      getenv("EDGE_TENANT_ID", "00000000-0000-0000-0000-000000000001"),
		TCPListen:     getenv("EDGE_TCP_LISTEN", ":9000"),
		APIURL:        getenv("EDGE_API_URL", "http://localhost:8000"),
		MQTTBroker:    getenv("EDGE_MQTT_BROKER", "tcp://localhost:1883"),
		DeviceAPIKey:  getenv("EDGE_DEVICE_API_KEY", "dev_device_key_change_me"),
		InternalKey:   getenv("API_INTERNAL_KEY", ""),
		MetricsAddr:   getenv("EDGE_METRICS_ADDR", ":9090"),
		Firmware:      getenv("EDGE_FIRMWARE", "0.1.0"),
		HeartbeatSec:  30,
		SyncIntervalS: 120,
		DataDir:       getenv("EDGE_DATA_DIR", "./data"),
	}
}

func getenv(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}
