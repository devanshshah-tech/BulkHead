package server

import (
	"context"
	"strings"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	retrievalv1 "github.com/devanshshah-tech/BulkHead/apps/retrieval-service/gen/bulkhead/retrieval/v1"
	"github.com/devanshshah-tech/BulkHead/apps/retrieval-service/internal/store"
)

type Store interface {
	Search(ctx context.Context, embedding []float32, topK int, corpusRef string) ([]store.Chunk, error)
	Ping(ctx context.Context) error
}

type Embedder interface {
	Embed(ctx context.Context, text string) ([]float32, error)
}

type Options struct {
	DefaultTopK int
	MaxTopK     int
}

type RetrievalServer struct {
	retrievalv1.UnimplementedRetrievalServiceServer
	store Store
	embed Embedder
	opts  Options
}

func New(st Store, emb Embedder, opts Options) *RetrievalServer {
	if opts.DefaultTopK <= 0 {
		opts.DefaultTopK = 5
	}
	if opts.MaxTopK <= 0 {
		opts.MaxTopK = 20
	}
	return &RetrievalServer{store: st, embed: emb, opts: opts}
}

func (s *RetrievalServer) Retrieve(ctx context.Context, req *retrievalv1.RetrieveRequest) (*retrievalv1.RetrieveResponse, error) {
	if strings.TrimSpace(req.GetQuery()) == "" {
		return nil, status.Error(codes.InvalidArgument, "query must not be empty")
	}

	topK := int(req.GetTopK())
	if topK <= 0 {
		topK = s.opts.DefaultTopK
	}
	if topK > s.opts.MaxTopK {
		topK = s.opts.MaxTopK
	}

	vec, err := s.embed.Embed(ctx, req.GetQuery())
	if err != nil {
		return nil, status.Errorf(codes.FailedPrecondition, "embed query: %v", err)
	}

	chunks, err := s.store.Search(ctx, vec, topK, req.GetCorpusRef())
	if err != nil {
		return nil, status.Errorf(codes.Internal, "vector search: %v", err)
	}

	resp := &retrievalv1.RetrieveResponse{}
	for _, c := range chunks {
		resp.Chunks = append(resp.Chunks, &retrievalv1.Chunk{
			ChunkId:        c.ID,
			DocId:          c.DocID,
			Source:         c.Source,
			Content:        c.Content,
			Score:          c.Score,
			CorpusCommit:   c.CorpusCommit,
			IngestedAtUnix: c.IngestedUnix,
		})
	}
	return resp, nil
}

func (s *RetrievalServer) Healthz(ctx context.Context, _ *retrievalv1.HealthzRequest) (*retrievalv1.HealthzResponse, error) {
	return &retrievalv1.HealthzResponse{DatabaseOk: s.store.Ping(ctx) == nil}, nil
}
