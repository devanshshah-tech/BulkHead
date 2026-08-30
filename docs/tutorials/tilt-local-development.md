# Local Development with Tilt and `mise`

This tutorial walks through using Tilt and `mise` to develop, test, and live-reload BulkHead microservices against a local k3d Kubernetes cluster.

## 1. Prerequisites

Ensure [`mise`](https://mise.jdx.dev) and Docker are installed on your workstation. Run:

```bash
mise install
```

This ensures `k3d`, `helm`, `kubectl`, `tilt`, `go`, and `python` match the pinned repository versions.

## 2. Launch the Development Environment

Run the single-command development task:

```bash
mise run dev
```

What `mise run dev` does under the hood:
1. Provisions a local lightweight `k3d` cluster named `bulkhead-dev`.
2. Installs Istio CRDs and the minimal mesh profile.
3. Deploys PostgreSQL/pgvector, MinIO, and lakeFS.
4. Starts `tilt up` to watch source code directories (`apps/ingestion-service`, `apps/retrieval-service`, `apps/query-api`).

## 3. The Tilt Live UI

Open `http://localhost:10350` in your browser. Tilt provides:
- Live streaming logs across all service pods.
- Fast container re-builds upon file modification.
- Live resource status and restart controls.

## 4. Testing Code Changes

Edit any Python or Go source file under `apps/`. Tilt automatically synchronizes the changed files directly into the active running containers without requiring full cluster teardown.

## 5. Running Automated Test Suites

To execute unit and integration tests across all microservices:

```bash
# Run all test suites
mise run test

# Run linter and formatting checks
mise run lint
```
