package embedclient

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type Client struct {
	endpoint string
	http     *http.Client
}

func New(endpoint string, timeout time.Duration) *Client {
	return &Client{
		endpoint: endpoint,
		http:     &http.Client{Timeout: timeout},
	}
}

type embedRequest struct {
	Texts []string `json:"texts"`
}

type embedResponse struct {
	Vectors [][]float32 `json:"vectors"`
	Dim     int         `json:"dim"`
}

func (c *Client) Embed(ctx context.Context, text string) ([]float32, error) {
	body, err := json.Marshal(embedRequest{Texts: []string{text}})
	if err != nil {
		return nil, err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.endpoint, bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, fmt.Errorf("embed request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(io.LimitReader(resp.Body, 512))
		return nil, fmt.Errorf("embed endpoint returned %d: %s", resp.StatusCode, string(b))
	}

	var out embedResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, fmt.Errorf("decode embed response: %w", err)
	}
	if len(out.Vectors) != 1 {
		return nil, fmt.Errorf("expected 1 vector, got %d", len(out.Vectors))
	}
	return out.Vectors[0], nil
}
