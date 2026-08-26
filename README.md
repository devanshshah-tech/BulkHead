# BulkHead

> A production-style Retrieval-Augmented Generation platform designed to run fully disconnected. Ships as a single Zarf airgap bundle, deployed via ArgoCD GitOps, with mTLS-secured service mesh (Istio), reproducible dev tooling (mise), and versioned document corpora (lakeFS). Includes a live connected-mode demo and a downloadable airgap bundle you can run yourself.

**Status:** under active construction — see [PLAN.md](PLAN.md) for the full execution plan.

![Architecture](docs/architecture/architecture.svg)

## Repository layout

| Path | Contents |
|---|---|
| `apps/ingestion-service` | FastAPI — chunk, embed, store documents; version corpus in lakeFS |
| `apps/query-api` | FastAPI — public REST + GraphQL, calls retrieval (gRPC) + local LLM |
| `apps/retrieval-service` | Go gRPC service — vector search against PostgreSQL/pgvector |
| `apps/inference` | Local model server config (Ollama) |
| `proto/` | gRPC service contracts |
| `infra/helm` | Helm charts per service + umbrella |
| `infra/istio` | Mesh policies: strict mTLS, gateway, traffic policy |
| `infra/zarf`, `infra/uds` | Airgap packaging |
| `infra/terraform` | Cloud infra for the connected demo |
| `gitops/argocd` | App-of-Apps manifests |
| `docs/` | Docusaurus site source |

## Quickstart (dev)

```sh
mise install        # pinned toolchain
mise run dev        # tilt up against local k3d cluster
```

All tasks: `mise run` with no arguments.
