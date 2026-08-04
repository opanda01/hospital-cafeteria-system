package mqttclient

import (
	"encoding/json"
	"fmt"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

type Client struct {
	deviceID string
	tenantID string
	client   mqtt.Client
}

func Connect(broker, deviceID, tenantID string) (*Client, error) {
	opts := mqtt.NewClientOptions().AddBroker(broker).SetClientID(fmt.Sprintf("edge-%s", deviceID))
	opts.SetAutoReconnect(true)
	opts.SetConnectRetry(true)
	opts.SetConnectRetryInterval(5 * time.Second)
	c := mqtt.NewClient(opts)
	token := c.Connect()
	if token.Wait() && token.Error() != nil {
		return nil, token.Error()
	}
	return &Client{deviceID: deviceID, tenantID: tenantID, client: c}, nil
}

func (c *Client) PublishEvent(payload any) error {
	topic := fmt.Sprintf("yemekhane/%s/devices/%s/events", c.tenantID, c.deviceID)
	raw, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	token := c.client.Publish(topic, 1, false, raw)
	token.Wait()
	return token.Error()
}

func (c *Client) PublishHeartbeat(payload any) error {
	topic := fmt.Sprintf("yemekhane/%s/devices/%s/heartbeat", c.tenantID, c.deviceID)
	raw, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	token := c.client.Publish(topic, 0, false, raw)
	token.Wait()
	return token.Error()
}

func (c *Client) Connected() bool {
	return c.client.IsConnected()
}

func (c *Client) Disconnect() {
	c.client.Disconnect(250)
}
