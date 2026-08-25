package config

import (
	"os"
	"time"
)

type Config struct {
	GRPCPort      string
	DatabaseURL   string
	EmbedEndpoint string
	EmbedTimeout  time.Duration
	DefaultTopK   int
	MaxTopK       int
}

func Load() Config {
	return Config{
		GRPCPort:      envOr("RETRIEVAL_PORT", "50051"),
		DatabaseURL:   envOr("RETRIEVAL_DATABASE_URL", "postgres://bulkhead:bulkhead@localhost:5432/vectors"),
		EmbedEndpoint: envOr("RETRIEVAL_EMBED_ENDPOINT", "http://ingestion-service:8001/internal/embeddings"),
		EmbedTimeout:  30 * time.Second,
		DefaultTopK:   5,
		MaxTopK:       20,
	}
}

func envOr(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}
