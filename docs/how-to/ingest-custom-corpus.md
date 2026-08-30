# Ingest Custom Documents and Version Corpora with lakeFS

BulkHead provides a traceable RAG pipeline: every ingested document is chunked, embedded, saved to Postgres (`pgvector`), backed up to MinIO, and committed to a **lakeFS repository**. This allows queries to be audited against immutable corpus commits.

## 1. Prepare Document Corpus

Documents can be plain text, markdown, or code files. For multi-file ingestion, prepare your files locally:

```bash
mkdir -p corpus
cat << 'EOF' > corpus/safety-protocols.md
# Airgap Safety Protocols
Bulkhead nodes must never route packets to public CIDR blocks.
All egress gateways are disabled by default.
EOF
```

## 2. Ingest via the REST API

Port-forward the ingestion service if running locally or in k3d:

```bash
kubectl -n bulkhead port-forward svc/ingestion-service 8001:8001 &
```

Upload each document:

```bash
curl -X POST http://localhost:8001/ingest \
  -F "file=@corpus/safety-protocols.md"
```

**Response:**

```json
{
  "status": "success",
  "doc_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "filename": "safety-protocols.md",
  "chunks_created": 2,
  "lakefs_commit": "c4d28e70f8016bc3e26f582f349386d4e4f509e5",
  "lakefs_branch": "main"
}
```

## 3. Verify Vector Storage in Postgres

To inspect the raw embeddings stored in PostgreSQL:

```bash
kubectl -n bulkhead exec -it deploy/postgres -c postgres -- \
  psql -U bulkhead -d bulkhead -c \
  "SELECT id, doc_id, chunk_index, LEFT(content, 60) AS snippet FROM document_chunks LIMIT 5;"
```

## 4. Audit Corpus Commits in lakeFS

lakeFS maintains git-like version control over all raw ingested blobs:

```bash
kubectl -n bulkhead port-forward svc/lakefs 8000:8000 &
```

Open `http://localhost:8000` in your browser (or use the `lakectl` CLI) to view commit histories, branches, and diffs for the `bulkhead-corpus` repository.
