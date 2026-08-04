package main

import (
	"encoding/json"
	"fmt"
	"net"
	"os"
	"time"
)

func main() {
	target := getenv("SIM_TARGET", "localhost:9000")
	cards := []string{"A1B2C3D4", "E5F6G7H8", "A1B2C3D4"}
	for {
		for _, uid := range cards {
			if err := sendCard(target, uid); err != nil {
				fmt.Printf("send error: %v\n", err)
			}
			time.Sleep(3 * time.Second)
		}
	}
}

func sendCard(target, uid string) error {
	conn, err := net.Dial("tcp", target)
	if err != nil {
		return err
	}
	defer conn.Close()
	payload, _ := json.Marshal(map[string]string{"card_uid": uid})
	_, err = conn.Write(append(payload, '\n'))
	return err
}

func getenv(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}
