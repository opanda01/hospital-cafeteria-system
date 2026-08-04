package cache

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"

	_ "modernc.org/sqlite"
)

type Store struct {
	db *sql.DB
}

func Open(dir string) (*Store, error) {
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return nil, err
	}
	path := filepath.Join(dir, "edge.db")
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	s := &Store{db: db}
	if err := s.migrate(); err != nil {
		return nil, err
	}
	return s, nil
}

func (s *Store) migrate() error {
	_, err := s.db.Exec(`
		CREATE TABLE IF NOT EXISTS cards (
			kart_uid TEXT PRIMARY KEY,
			user_id INTEGER NOT NULL,
			aktif INTEGER NOT NULL DEFAULT 1
		);
		CREATE TABLE IF NOT EXISTS entitlements (
			user_id INTEGER NOT NULL,
			meal_id INTEGER NOT NULL,
			kalan_hak INTEGER NOT NULL,
			PRIMARY KEY (user_id, meal_id)
		);
		CREATE TABLE IF NOT EXISTS meta (
			key TEXT PRIMARY KEY,
			value TEXT NOT NULL
		);
	`)
	return err
}

func (s *Store) SetCacheVersion(v int) error {
	_, err := s.db.Exec(`INSERT INTO meta(key,value) VALUES('cache_version', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value`, fmt.Sprint(v))
	return err
}

func (s *Store) CacheVersion() int {
	var v string
	err := s.db.QueryRow(`SELECT value FROM meta WHERE key='cache_version'`).Scan(&v)
	if err != nil {
		return 0
	}
	var n int
	fmt.Sscanf(v, "%d", &n)
	return n
}

func (s *Store) ReplaceCards(uids map[string]int) error {
	tx, err := s.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if _, err := tx.Exec(`DELETE FROM cards`); err != nil {
		return err
	}
	for uid, userID := range uids {
		if _, err := tx.Exec(`INSERT INTO cards(kart_uid,user_id,aktif) VALUES(?,?,1)`, uid, userID); err != nil {
			return err
		}
	}
	return tx.Commit()
}

func (s *Store) ReplaceEntitlements(items map[string]int) error {
	tx, err := s.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if _, err := tx.Exec(`DELETE FROM entitlements`); err != nil {
		return err
	}
	for key, kalan := range items {
		var userID, mealID int
		fmt.Sscanf(key, "%d:%d", &userID, &mealID)
		if _, err := tx.Exec(`INSERT INTO entitlements(user_id,meal_id,kalan_hak) VALUES(?,?,?)`, userID, mealID, kalan); err != nil {
			return err
		}
	}
	return tx.Commit()
}

func (s *Store) CardAllowed(uid string) (bool, string) {
	var userID int
	var aktif int
	err := s.db.QueryRow(`SELECT user_id, aktif FROM cards WHERE kart_uid=?`, uid).Scan(&userID, &aktif)
	if err != nil {
		return false, "RED_KART_GECERSIZ"
	}
	if aktif != 1 {
		return false, "RED_KART_GECERSIZ"
	}
	return true, "ALLOW"
}

func (s *Store) Close() error {
	return s.db.Close()
}
