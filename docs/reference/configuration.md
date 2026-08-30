# Configuration & Environment Variables

This document lists all environment variables, ports, and configuration options across BulkHead services.

## 1. `apps/ingestion-service`

| Variable | Type | Default | Description |
|---|---|---|---|
| `PORT` | int | `8001` | HTTP server port |
| `POSTGRES_HOST` | string | `postgres.bulkhead.svc.cluster.local` | Database hostname |
| `POSTGRES_PORT` | int | `5432` | Database port |
| `POSTGRES_DB` | string | `bulkhead` | Database name |
| `POSTGRES_USER` | string | `bulkhead` | Database user |
| `POSTGRES_PASSWORD` | string | - | Database password |
| `MINIO_ENDPOINT` | string | `minio.bulkhead.svc.cluster.local:9000` | S3 endpoint |
| `MINIO_ACCESS_KEY` | string | `minioadmin` | S3 access key |
| `MINIO_SECRET_KEY` | string | - | S3 secret key |
| `LAKEFS_ENDPOINT` | string | `http://lakefs.bulkhead.svc.cluster.local:8000` | lakeFS server URL |
| `EMBEDDING_MODEL` | string | `all-MiniLM-L6-v2` | Baked-in embedding model name |

---

## 2. `apps/retrieval-service` (Go gRPC)

| Variable | Type | Default | Description |
|---|---|---|---|
| `GRPC_PORT` | int | `50051` | gRPC server listening port |
| `DATABASE_URL` | string | `postgres://bulkhead:...@postgres:5432/bulkhead` | Postgres connection string |
| `TOP_K_DEFAULT` | int | `5` | Default number of vector chunks retrieved |
| `INGESTION_SERVICE_URL` | string | `http://ingestion-service.bulkhead.svc.cluster.local:8001` | Ingestion service for query embedding |

---

## 3. `apps/query-api`

| Variable | Type | Default | Description |
|---|---|---|---|
| `PORT` | int | `8002` | HTTP listening port |
| `RETRIEVAL_GRPC_ADDR` | string | `retrieval-service.bulkhead.svc.cluster.local:50051` | Retrieval service gRPC target |
| `OLLAMA_HOST` | string | `http://ollama.bulkhead.svc.cluster.local:11434` | Ollama local inference endpoint |
| `MODEL_NAME` | string | `llama3.2:1b` | Model name loaded in Ollama |
| `MAX_TOKENS` | int | `512` | Maximum generated tokens per answer |

---

## 4. `apps/inference` (Ollama)

| Variable | Type | Default | Description |
|---|---|---|---|
| `OLLAMA_HOST` | string | `0.0.0.0:11434` | Inference bind address |
| `OLLAMA_MODELS` | string | `/root/.ollama/models` | Local directory containing baked GGUF weights |
| `OLLAMA_NUM_PARALLEL` | int | `2` | Number of parallel inference requests |
