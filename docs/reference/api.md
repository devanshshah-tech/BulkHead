# REST API — query-api

The public entrypoint. FastAPI, exposed through the Istio ingress gateway.

## `POST /query`

Grounded question answering: retrieves top-k chunks via gRPC, generates an answer with the local model, returns citations.

**Request**

```json
{ "question": "What is Bulkhead?" }
```

**Response `200`**

```json
{
  "answer": "Bulkhead deploys a RAG stack as a single UDS bundle… [1]",
  "citations": [
    { "chunk_id": "e2cd7ed7-…", "doc_id": "f3c22222-…",
      "source": "bulkhead-doc.txt", "content": "…" }
  ]
}
```

**Errors**

| Code | Cause |
|---|---|
| 422 | missing/invalid `question` field |
| 500 | retrieval or inference backend unreachable |

## `GET /healthz`

Liveness. Returns `{"status":"ok"}`.

## `GET /readyz`

Readiness — checks gRPC connectivity to the retrieval service.

---

# REST API — ingestion-service

## `POST /ingest`

Multipart upload (`file=@doc.txt`). Chunks, embeds with `all-MiniLM-L6-v2` (baked in, offline), writes vectors to pgvector and the raw file to MinIO; tags the run with a lakeFS commit so answers trace to corpus versions.

## `POST /internal/embeddings`

gRPC-adjacent internal endpoint used by the retrieval service for query embedding.
