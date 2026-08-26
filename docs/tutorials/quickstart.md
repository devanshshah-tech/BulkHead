# Quickstart: from zero to a grounded answer

Learn how to deploy BulkHead's full RAG stack into a local Kubernetes cluster and ask it a question — with zero internet access at deploy time.

## What you'll build

```mermaid
ingest → chunk+embed → pgvector → retrieve (gRPC) → llama3.2:1b → cited answer
```

## Prerequisites

- Docker Desktop (≥ 4 GB RAM free) and k3d
- The UDS bundle for your architecture from [GitHub Releases](https://github.com/devanshshah-tech/BulkHead/releases)
- `uds` CLI ([install](https://uds.defenseunicorns.com/))

## 1. Create a scratch cluster

```bash
k3d cluster create bulkhead-demo
```

## 2. Deploy the bundle

```bash
uds deploy uds-bundle-bulkhead-rag-arm64-v0.1.1.tar.zst --confirm
```

Everything — Postgres/pgvector, MinIO, lakeFS, Istio, Ollama with baked weights, and the three services — installs offline. Wait ~5 minutes.

## 3. Ingest a document

```bash
kubectl -n bulkhead port-forward svc/ingestion-service 8001:8001 &
echo "BulkHead is an airgap-deployable RAG platform." > doc.txt
curl -s -X POST localhost:8001/ingest -F file=@doc.txt
```

## 4. Ask a question

```bash
kubectl -n bulkhead port-forward svc/query-api 8002:8002 &
curl -s -X POST localhost:8002/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is BulkHead?"}'
```

You get a grounded answer plus citations pointing at the ingested chunks.

## Next steps

- Run the fully egress-blocked version: [Prove the airgap](./airgap-proof)
- Understand what got deployed: [Architecture](../explanation/architecture)
