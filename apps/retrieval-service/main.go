package main

import (
	"context"
	"log/slog"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"google.golang.org/grpc"

	retrievalv1 "github.com/devanshshah-tech/BulkHead/apps/retrieval-service/gen/bulkhead/retrieval/v1"
	"github.com/devanshshah-tech/BulkHead/apps/retrieval-service/internal/config"
	"github.com/devanshshah-tech/BulkHead/apps/retrieval-service/internal/embedclient"
	"github.com/devanshshah-tech/BulkHead/apps/retrieval-service/internal/server"
	"github.com/devanshshah-tech/BulkHead/apps/retrieval-service/internal/store"
)

func connectWithRetry(ctx context.Context, url string, logger *slog.Logger) (*store.Store, error) {
	var st *store.Store
	var err error
	for attempt := 1; attempt <= 30; attempt++ {
		st, err = store.New(ctx, url)
		if err == nil {
			return st, nil
		}
		logger.Warn("vector store not ready, retrying", "attempt", attempt, "error", err)
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-time.After(2 * time.Second):
		}
	}
	return nil, err
}

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	cfg := config.Load()

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	st, err := connectWithRetry(ctx, cfg.DatabaseURL, logger)
	if err != nil {
		logger.Error("failed to connect vector store", "error", err)
		os.Exit(1)
	}
	defer st.Close()

	svc := server.New(
		st,
		embedclient.New(cfg.EmbedEndpoint, cfg.EmbedTimeout),
		server.Options{DefaultTopK: cfg.DefaultTopK, MaxTopK: cfg.MaxTopK},
	)

	lis, err := net.Listen("tcp", ":"+cfg.GRPCPort)
	if err != nil {
		logger.Error("failed to listen", "port", cfg.GRPCPort, "error", err)
		os.Exit(1)
	}

	gs := grpc.NewServer()
	retrievalv1.RegisterRetrievalServiceServer(gs, svc)

	go func() {
		<-ctx.Done()
		logger.Info("shutting down")
		gs.GracefulStop()
	}()

	logger.Info("retrieval-service listening", "port", cfg.GRPCPort, "embed_endpoint", cfg.EmbedEndpoint)
	if err := gs.Serve(lis); err != nil {
		logger.Error("grpc serve", "error", err)
		os.Exit(1)
	}
}
