#!/usr/bin/env bash
# Phase 4 deliverable: prove the airgap claim.
#
# Deploys the UDS bundle to a k3d cluster running on a docker --internal
# network (no gateway => no route to the internet). Everything the platform
# needs comes out of the bundle; the only pre-seeded images are the four k3s
# system images (coredns, local-path-provisioner, metrics-server, pause) which
# a stock cluster would otherwise try to pull at bootstrap.
#
# Usage: ./hack/deploy-airgap.sh [--yes] [path/to/bundle.tar.zst]
#   --yes                      delete an existing 'airgap-sim' cluster without asking (wipes its PVCs)
#   positional bundle path     overrides the default local build output
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$PWD"
export PATH="$ROOT/bin:$PATH"

CLUSTER="airgap-sim"
NET="airgap-none"
BUNDLE="build/uds-bundle-bulkhead-rag-arm64-0.1.1.tar.zst"
for arg in "$@"; do
  case "$arg" in
    --yes) ;;
    *) BUNDLE="$arg" ;;
  esac
done

SYSTEM_IMAGES=(
  "docker.io/rancher/local-path-provisioner:v0.0.36"
  "docker.io/rancher/mirrored-coredns-coredns:1.14.3"
  "docker.io/rancher/mirrored-metrics-server:v0.8.1"
  "docker.io/rancher/mirrored-pause:3.6"
)

for tool in docker k3d kubectl uds zarf; do
  command -v "$tool" >/dev/null || { echo "$tool not found in PATH" >&2; exit 1; }
done

# ---------------------------------------------------------------------------
# 1. Bundle must exist (build it if missing)
# ---------------------------------------------------------------------------
if [ ! -f "$BUNDLE" ]; then
  echo "==> bundle missing, building packages first"
  ./hack/package.sh
fi

# ---------------------------------------------------------------------------
# 2. Teardown (destructive: wipes cluster + PVC data) — requires --yes if exists
# ---------------------------------------------------------------------------
if k3d cluster list 2>/dev/null | grep -q "^$CLUSTER\b" && [ "${1:-}" != "--yes" ]; then
  echo "cluster '$CLUSTER' already exists." >&2
  echo "re-running deletes it INCLUDING corpus/database volumes." >&2
  echo "confirm with: $0 --yes" >&2
  exit 1
fi
k3d cluster delete "$CLUSTER" >/dev/null 2>&1 || true
docker network rm "$NET" >/dev/null 2>&1 || true

# Internal network: no default gateway, containers cannot reach the internet
docker network create --internal "$NET" >/dev/null
echo "==> created egress-blocked docker network '$NET'"

# ---------------------------------------------------------------------------
# 3. Seed the k3s system images (only non-bundle images the node needs)
# ---------------------------------------------------------------------------
for img in "${SYSTEM_IMAGES[@]}"; do
  docker pull -q "$img" >/dev/null 2>&1 || { echo "failed to pull $img (needed before going offline)" >&2; exit 1; }
done

# ---------------------------------------------------------------------------
# 4. Cluster inside the walled network
# ---------------------------------------------------------------------------
k3d cluster create "$CLUSTER" \
  --network "$NET" \
  --k3s-arg '--disable=traefik@server:0' \
  -p "31999:31999@loadbalancer" >/dev/null

kubectl config use-context "k3d-$CLUSTER" >/dev/null
echo "==> cluster '$CLUSTER' up (no outbound internet)"

k3d image import "${SYSTEM_IMAGES[@]}" -c "$CLUSTER" >/dev/null
echo "==> seeded ${#SYSTEM_IMAGES[@]} system images into the node"

# ---------------------------------------------------------------------------
# 5. Deploy the platform — only from the bundle
# ---------------------------------------------------------------------------
echo "==> uds deploy (offline)"
uds deploy "$BUNDLE" --confirm --no-log-file

# ---------------------------------------------------------------------------
# 6. Verify the stack is healthy
# ---------------------------------------------------------------------------
echo "==> waiting for workloads"
for dep in postgres minio lakefs ollama retrieval-service ingestion-service query-api; do
  kubectl -n bulkhead rollout status "deploy/$dep" --timeout=600s ||
    kubectl -n bulkhead rollout status "statefulset/$dep" --timeout=300s
done

cat <<'EOF'

=============================================================
 Airgap deployment complete — proof commands for the recording:

 # 1. show egress is blocked (must FAIL / time out):
 kubectl -n bulkhead exec deploy/ollama -c ollama -- curl -m 5 -sS https://example.com

 # 2. run a grounded query entirely inside the cluster:
 kubectl -n bulkhead port-forward svc/query-api 8002:8002 &
 curl -s -X POST localhost:8002/query -H 'Content-Type: application/json' \
   -d '{"question":"<your question>"}'

 # 3. show the model came from the bundle (no pulls):
 kubectl -n bulkhead exec deploy/ollama -c ollama -- ollama list
=============================================================
EOF