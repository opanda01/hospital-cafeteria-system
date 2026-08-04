package tcpreader

import (
	"bufio"
	"encoding/json"
	"log"
	"net"
)

type CardEvent struct {
	CardUID string `json:"card_uid"`
}

type Handler func(cardUID string)

func Listen(addr string, handler Handler) error {
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return err
	}
	log.Printf("TCP reader listening on %s", addr)
	go func() {
		for {
			conn, err := ln.Accept()
			if err != nil {
				continue
			}
			go handleConn(conn, handler)
		}
	}()
	return nil
}

func handleConn(conn net.Conn, handler Handler) {
	defer conn.Close()
	sc := bufio.NewScanner(conn)
	for sc.Scan() {
		line := sc.Bytes()
		var evt CardEvent
		if err := json.Unmarshal(line, &evt); err != nil || evt.CardUID == "" {
			continue
		}
		handler(evt.CardUID)
	}
}
