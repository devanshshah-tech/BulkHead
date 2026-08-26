# mise tasks

All task definitions live in `.mise.toml`. List them with `mise run`.

| Task | What it does |
|---|---|
| `mise run lint` | ruff (Python services), gofmt/vet (Go retrieval service) |
| `mise run test` | pytest × 2 + `go test ./...` |
| `mise run proto` | regenerate gRPC stubs from `proto/` via buf |
| `mise run build` | local multi-stage image builds (`hack/build-images.sh`) |
| `mise run dev` | Tilt inner dev loop against k3d |
| `mise run deploy:local` | scratch k3d cluster + Helm deploy |
| `mise run package` | Zarf packages + UDS bundle → `build/` (`ARCH=` overrides target arch) |
| `mise run deploy:airgap` | egress-blocked cluster deploy from a bundle (`hack/deploy-airgap.sh`) |
| `mise run deploy:demo` | Terraform apply + wait for ArgoCD sync (connected demo) |

# Bundle contents

Each release ships two artifacts: `uds-bundle-bulkhead-rag-{amd64,arm64}-<ver>.tar.zst`, each containing:

| Zarf package | Carries |
|---|---|
| `bulkhead-mesh` | Istio base CRDs, istiod, ingress gateway (1.30.3) |
| `bulkhead-data` | Postgres/pgvector, MinIO, lakeFS images |
| `bulkhead-inference` | CPU-only Ollama + llama3.2:1b **Q4_K_M weights baked in** |
| `bulkhead-apps` | ingestion-service, retrieval-service, query-api |

No component contacts the internet at deploy time.

# CI pipeline

`.github/workflows/ci.yml`, triggered on push/PR/tags:

1. **test** — matrix over the three services
2. **build-push** — multi-arch (amd64+arm64) images → ghcr.io, tagged `latest` *and* `${git-sha}`
3. **publish-bundle** *(v\* tags)* — dual-arch Zarf packages + UDS bundle → GitHub Release assets, enforced ≤ 2 GiB
