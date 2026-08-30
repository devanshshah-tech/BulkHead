# BulkHead

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE.md)
[![CI](https://github.com/devanshshah-tech/BulkHead/actions/workflows/ci.yml/badge.svg)](https://github.com/devanshshah-tech/BulkHead/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/devanshshah-tech/BulkHead?include_prereleases&color=brightgreen)](https://github.com/devanshshah-tech/BulkHead/releases)
[![Architecture](https://img.shields.io/badge/arch-amd64%20%7C%20arm64-informational)](#bundle-distribution)

> **A production-style Retrieval-Augmented Generation (RAG) platform engineered to run fully disconnected.**  
> Ships as a single [Zarf](https://zarf.dev)/[UDS](https://uds.defenseunicorns.com) airgap bundle, deployed via ArgoCD GitOps, secured with an Istio mTLS service mesh, managed with reproducible dev tooling ([`mise`](https://mise.jdx.dev)), and backed by immutable document corpora versioning ([lakeFS](https://lakefs.io)).

---

## 🏛 Architecture

BulkHead enforces a **zero-egress, offline-first** boundary. All embeddings, LLM inference, vector storage, and data pipelines operate inside the Kubernetes cluster with zero external API calls.

![BulkHead Architecture](docs/architecture/architecture.svg)

### Service Components

| Component | Stack | Responsibilities |
|---|---|---|
| **Ingestion Service** | Python, FastAPI, `sentence-transformers` | Ingests documents, generates embeddings with baked-in `all-MiniLM-L6-v2`, writes vectors to pgvector & raw documents to MinIO, and commits immutable corpus versions to lakeFS. |
| **Retrieval Service** | Go 1.22+, gRPC, `pgx` | Internal-only vector search service. Communicates over high-performance gRPC, queries pgvector with cosine similarity / HNSW indexing, and enforces strict mesh policies. |
| **Query API** | Python, FastAPI, gRPC Client | Public API gateway for RAG inference. Accepts user queries, embeds questions, calls retrieval over gRPC, constructs prompt contexts, and streams answers with citations. |
| **Inference Server** | Ollama (CPU-only, `llama3.2:1b` Q4_K_M) | Self-hosted local inference with quantized weights baked directly into the container image. Zero API keys, zero network phone-home. |
| **Data Layer** | PostgreSQL + `pgvector`, MinIO, lakeFS | Unified relational + vector storage, S3-compatible raw object store, and git-like branchable corpus data management. |
| **Service Mesh & Security** | Istio 1.22+ (`PeerAuthentication: STRICT`) | Cryptographic service-to-service mTLS, Istio Ingress Gateway, traffic routing, and egress-blocking network isolation policies. |

---

## 💼 Skills & Technology Matrix

| Discipline | Technologies Used | Platform Implementation in BulkHead |
|---|---|---|
| **Platform Packaging & Airgap** | Zarf, UDS CLI | Declarative multi-package bundles containing OCI images, Helm charts, and baked GGUF weights in a single `.tar.zst` payload (`< 2 GiB`). |
| **Service Mesh & Zero Trust** | Istio, Envoy | In-mesh STRICT mTLS, Ingress routing, egress traffic policies, and container network isolation. |
| **GitOps & Delivery** | ArgoCD, Helm 3, Helmfile | App-of-Apps GitOps management reconciling declarative charts for connected and airgap environments. |
| **Infrastructure as Code** | Terraform, Terraform Cloud | Reproducible cloud cluster provisioning and DNS automation. |
| **AI / RAG Engineering** | FastAPI, Go gRPC, pgvector, Ollama | Microservice RAG pipeline, local CPU-only quantized LLM inference, embedding generation, and citation provenance. |
| **Data Lifecycle & Versioning** | lakeFS, MinIO, PostgreSQL | Git-style versioning for document corpora enabling immutable audit trails for generated answers. |
| **Developer Experience (DX)** | `mise`, Tilt, k3d | Pinned toolchains, single-command live development loops (`mise run dev`), and automated testing suites. |

---

## ⚡ Quickstart

### Option A: Local Airgap Evaluation (Single Command)

Test BulkHead in a simulated disconnected cluster with **no outbound internet access**:

1. **Download the bundle** from [GitHub Releases](https://github.com/devanshshah-tech/BulkHead/releases/latest):
   ```bash
   # For macOS Apple Silicon / ARM64 Linux:
   curl -LO https://github.com/devanshshah-tech/BulkHead/releases/download/v0.1.1/uds-bundle-bulkhead-rag-arm64-0.1.1.tar.zst

   # For x86_64 / AMD64 Linux:
   curl -LO https://github.com/devanshshah-tech/BulkHead/releases/download/v0.1.1/uds-bundle-bulkhead-rag-amd64-0.1.1.tar.zst
   ```

2. **Deploy to a zero-egress cluster**:
   ```bash
   ./hack/deploy-airgap.sh --yes uds-bundle-bulkhead-rag-arm64-0.1.1.tar.zst
   ```
   *(Creates a k3d cluster with network egress disabled, loads the UDS bundle, and provisions the entire stack offline).*

3. **Verify offline status & query the platform**:
   ```bash
   # 1. Verify outbound internet is completely blocked (returns connection failure)
   kubectl -n bulkhead exec deploy/ollama -c ollama -- curl -m 5 -sS https://example.com

   # 2. Ingest sample document
   kubectl -n bulkhead port-forward svc/ingestion-service 8001:8001 &
   curl -s -X POST localhost:8001/ingest -F file=@docs/explanation/architecture.md
   kill %1

   # 3. Ask a grounded question
   kubectl -n bulkhead port-forward svc/query-api 8002:8002 &
   curl -s -X POST localhost:8002/query \
     -H 'Content-Type: application/json' \
     -d '{"question":"What are the responsibilities of the retrieval service?"}'
   kill %1
   ```

---

### Option B: Local Development Loop (Tilt + `mise`)

For rapid service iteration and development:

```bash
# 1. Install pinned tools (python, go, k3d, helm, zarf, uds, tilt)
mise install

# 2. Start the inner dev loop (spins up local k3d cluster & launches Tilt live reload)
mise run dev
```

All available tasks can be inspected with `mise tasks`.

---

## 📦 Repository Layout

```
bulkhead-rag/
├── apps/
│   ├── ingestion-service/     # FastAPI document chunking, embedding & lakeFS commits
│   ├── query-api/              # FastAPI public REST API & gRPC orchestrator
│   ├── retrieval-service/      # Go gRPC vector search engine (pgvector)
│   └── inference/              # Ollama container with baked Llama 3.2 1B Q4_K_M weights
├── proto/                      # Protobuf service contracts (buf managed)
├── infra/
│   ├── helm/                   # Helm charts (umbrella + sub-charts)
│   ├── istio/                  # Mesh security, mTLS PeerAuthentication & Ingress
│   ├── zarf/                   # Declarative Zarf packaging specs (mesh, data, inference, apps)
│   ├── uds/                    # UDS bundle definitions & dependency DAG
│   └── terraform/              # Cloud VM and remote state configuration
├── gitops/
│   └── argocd/                 # App-of-Apps declarative GitOps manifests
├── hack/                       # Automation scripts for packaging & airgap verification
├── docs/                       # Diátaxis documentation suite (Docusaurus)
└── .mise.toml                  # Pinned developer toolchain & automation tasks
```

---

## 📖 Deep Dives & Documentation

- [Architecture & Data Flow](docs/explanation/architecture.md)
- [Key Design Decisions & Tradeoffs](docs/explanation/design-decisions.md)
- [REST & gRPC API Reference](docs/reference/api.md)
- [Airgap Proof Runbook](docs/tutorials/airgap-proof.md)
- [Model Swapping Guide](docs/how-to/swap-the-model.md)

---

## 📄 License

Licensed under the [Apache License, Version 2.0](LICENSE.md).
