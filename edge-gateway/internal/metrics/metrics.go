package metrics

import (
	"net/http"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	EventsTotal = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "edge_events_total",
		Help: "Total card read events processed",
	})
	QueueDepth = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "edge_queue_depth",
		Help: "Offline queue depth",
	})
	MQTTConnected = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "edge_mqtt_connected",
		Help: "1 if MQTT connected",
	})
)

func init() {
	prometheus.MustRegister(EventsTotal, QueueDepth, MQTTConnected)
}

func Serve(addr string) error {
	mux := http.NewServeMux()
	mux.Handle("/metrics", promhttp.Handler())
	return http.ListenAndServe(addr, mux)
}
