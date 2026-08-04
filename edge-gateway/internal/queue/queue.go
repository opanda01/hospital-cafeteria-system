package queue

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
)

type Item struct {
	Kind    string          `json:"kind"`
	Payload json.RawMessage `json:"payload"`
}

type DiskQueue struct {
	path string
	mu   sync.Mutex
}

func Open(dir string) (*DiskQueue, error) {
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return nil, err
	}
	return &DiskQueue{path: filepath.Join(dir, "queue.jsonl")}, nil
}

func (q *DiskQueue) Push(kind string, payload any) error {
	q.mu.Lock()
	defer q.mu.Unlock()
	raw, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	item := Item{Kind: kind, Payload: raw}
	line, err := json.Marshal(item)
	if err != nil {
		return err
	}
	f, err := os.OpenFile(q.path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = f.Write(append(line, '\n'))
	return err
}

func (q *DiskQueue) Depth() int {
	q.mu.Lock()
	defer q.mu.Unlock()
	data, err := os.ReadFile(q.path)
	if err != nil {
		return 0
	}
	if len(data) == 0 {
		return 0
	}
	n := 0
	for _, b := range data {
		if b == '\n' {
			n++
		}
	}
	return n
}

func (q *DiskQueue) Drain(handler func(Item) error) error {
	q.mu.Lock()
	defer q.mu.Unlock()
	data, err := os.ReadFile(q.path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}
	_ = os.WriteFile(q.path, nil, 0o644)
	lines := splitLines(data)
	for _, line := range lines {
		var item Item
		if err := json.Unmarshal(line, &item); err != nil {
			continue
		}
		if err := handler(item); err != nil {
			_ = q.appendRaw(line)
		}
	}
	return nil
}

func (q *DiskQueue) appendRaw(line []byte) error {
	f, err := os.OpenFile(q.path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = f.Write(append(line, '\n'))
	return err
}

func splitLines(data []byte) [][]byte {
	var out [][]byte
	start := 0
	for i, b := range data {
		if b == '\n' {
			if i > start {
				out = append(out, data[start:i])
			}
			start = i + 1
		}
	}
	if start < len(data) {
		out = append(out, data[start:])
	}
	return out
}
