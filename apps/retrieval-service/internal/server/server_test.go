package server

import (
	"context"
	"errors"
	"net"
	"testing"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"
	"google.golang.org/grpc/test/bufconn"

	retrievalv1 "github.com/devanshshah-tech/BulkHead/apps/retrieval-service/gen/bulkhead/retrieval/v1"
	"github.com/devanshshah-tech/BulkHead/apps/retrieval-service/internal/store"
)

type fakeStore struct {
	chunks   []store.Chunk
	pingErr  error
	lastTopK int
	lastRef  string
}

func (f *fakeStore) Search(_ context.Context, _ []float32, topK int, corpusRef string) ([]store.Chunk, error) {
	f.lastTopK = topK
	f.lastRef = corpusRef
	if len(f.chunks) > topK {
		return f.chunks[:topK], nil
	}
	return f.chunks, nil
}

func (f *fakeStore) Ping(context.Context) error { return f.pingErr }

type fakeEmbedder struct {
	err error
}

func (f *fakeEmbedder) Embed(context.Context, string) ([]float32, error) {
	if f.err != nil {
		return nil, f.err
	}
	return []float32{0.1, 0.2, 0.3}, nil
}

func startTestServer(t *testing.T, st Store, emb Embedder) retrievalv1.RetrievalServiceClient {
	t.Helper()
	lis := bufconn.Listen(1024 * 1024)
	gs := grpc.NewServer()
	retrievalv1.RegisterRetrievalServiceServer(gs, New(st, emb, Options{DefaultTopK: 5, MaxTopK: 10}))
	go gs.Serve(lis)
	t.Cleanup(gs.Stop)

	conn, err := grpc.NewClient("passthrough:///bufnet",
		grpc.WithContextDialer(func(ctx context.Context, _ string) (net.Conn, error) {
			return lis.DialContext(ctx)
		}),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		t.Fatalf("dial bufconn: %v", err)
	}
	t.Cleanup(func() { conn.Close() })
	return retrievalv1.NewRetrievalServiceClient(conn)
}

func TestRetrieveMapsChunks(t *testing.T) {
	st := &fakeStore{chunks: []store.Chunk{{
		ID: "c1", DocID: "d1", Source: "doc.txt", Content: "hello",
		Score: 0.91, CorpusCommit: "abc123", IngestedUnix: 1700000000,
	}}}
	client := startTestServer(t, st, &fakeEmbedder{})

	resp, err := client.Retrieve(context.Background(), &retrievalv1.RetrieveRequest{Query: "hello", TopK: 3, CorpusRef: "abc123"})
	if err != nil {
		t.Fatalf("Retrieve: %v", err)
	}
	if len(resp.Chunks) != 1 {
		t.Fatalf("expected 1 chunk, got %d", len(resp.Chunks))
	}
	c := resp.Chunks[0]
	if c.ChunkId != "c1" || c.DocId != "d1" || c.CorpusCommit != "abc123" {
		t.Fatalf("unexpected chunk mapping: %+v", c)
	}
	if st.lastTopK != 3 || st.lastRef != "abc123" {
		t.Fatalf("store called with topK=%d ref=%q", st.lastTopK, st.lastRef)
	}
}

func TestRetrieveEmptyQuery(t *testing.T) {
	client := startTestServer(t, &fakeStore{}, &fakeEmbedder{})
	_, err := client.Retrieve(context.Background(), &retrievalv1.RetrieveRequest{Query: "   "})
	if status.Code(err) != codes.InvalidArgument {
		t.Fatalf("expected InvalidArgument, got %v", err)
	}
}

func TestRetrieveClampsTopK(t *testing.T) {
	st := &fakeStore{}
	client := startTestServer(t, st, &fakeEmbedder{})
	if _, err := client.Retrieve(context.Background(), &retrievalv1.RetrieveRequest{Query: "q", TopK: 999}); err != nil {
		t.Fatalf("Retrieve: %v", err)
	}
	if st.lastTopK != 10 {
		t.Fatalf("expected topK clamped to 10, got %d", st.lastTopK)
	}
	if _, err := client.Retrieve(context.Background(), &retrievalv1.RetrieveRequest{Query: "q"}); err != nil {
		t.Fatalf("Retrieve: %v", err)
	}
	if st.lastTopK != 5 {
		t.Fatalf("expected default topK 5, got %d", st.lastTopK)
	}
}

func TestRetrieveEmbedFailure(t *testing.T) {
	client := startTestServer(t, &fakeStore{}, &fakeEmbedder{err: errors.New("boom")})
	_, err := client.Retrieve(context.Background(), &retrievalv1.RetrieveRequest{Query: "q"})
	if status.Code(err) != codes.FailedPrecondition {
		t.Fatalf("expected FailedPrecondition, got %v", err)
	}
}

func TestHealthz(t *testing.T) {
	client := startTestServer(t, &fakeStore{}, &fakeEmbedder{})
	resp, err := client.Healthz(context.Background(), &retrievalv1.HealthzRequest{})
	if err != nil {
		t.Fatalf("Healthz: %v", err)
	}
	if !resp.DatabaseOk {
		t.Fatal("expected database_ok=true")
	}

	client = startTestServer(t, &fakeStore{pingErr: errors.New("down")}, &fakeEmbedder{})
	resp, err = client.Healthz(context.Background(), &retrievalv1.HealthzRequest{})
	if err != nil {
		t.Fatalf("Healthz: %v", err)
	}
	if resp.DatabaseOk {
		t.Fatal("expected database_ok=false")
	}
}
