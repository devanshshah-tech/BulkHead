package store

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5/pgxpool"
)

type Chunk struct {
	ID           string
	DocID        string
	Source       string
	Content      string
	Score        float32
	CorpusCommit string
	IngestedUnix int64
}

type Store struct {
	pool *pgxpool.Pool
}

func New(ctx context.Context, databaseURL string) (*Store, error) {
	pool, err := pgxpool.New(ctx, databaseURL)
	if err != nil {
		return nil, fmt.Errorf("connect pool: %w", err)
	}
	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("ping database: %w", err)
	}
	return &Store{pool: pool}, nil
}

func (s *Store) Close() { s.pool.Close() }

func (s *Store) Ping(ctx context.Context) error { return s.pool.Ping(ctx) }

func (s *Store) Search(ctx context.Context, embedding []float32, topK int, corpusRef string) ([]Chunk, error) {
	query := `SELECT chunk_id, doc_id, source, content, corpus_commit,
EXTRACT(EPOCH FROM ingested_at)::bigint AS ingested_unix,
1 - (embedding <=> $1::vector) AS score
FROM chunks`
	args := []any{VectorLiteral(embedding)}
	if corpusRef != "" {
		query += " WHERE corpus_commit = $2"
		args = append(args, corpusRef)
	}
	query += fmt.Sprintf(" ORDER BY embedding <=> $1::vector LIMIT %d", topK)

	rows, err := s.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("vector search: %w", err)
	}
	defer rows.Close()

	var out []Chunk
	for rows.Next() {
		var c Chunk
		if err := rows.Scan(&c.ID, &c.DocID, &c.Source, &c.Content, &c.CorpusCommit, &c.IngestedUnix, &c.Score); err != nil {
			return nil, fmt.Errorf("scan chunk: %w", err)
		}
		out = append(out, c)
	}
	return out, rows.Err()
}
