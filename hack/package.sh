#!/usr/bin/env bash
# Build the Zarf packages and compose them into the UDS airgap bundle.
# Output: build/uds-bundle-bulkhead-rag-<arch>-<ver>.tar.zst
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$PWD"

export PATH="$ROOT/bin:$PATH"
command -v zarf >/dev/null || { echo "zarf not found in ./bin" >&2; exit 1; }
command -v uds >/dev/null || { echo "uds not found in ./bin" >&2; exit 1; }

mkdir -p build

for pkg in bulkhead-mesh bulkhead-data bulkhead-inference bulkhead-apps; do
  echo "==> zarf package create $pkg"
  zarf package create "infra/zarf/${pkg}" \
    -o "infra/zarf/${pkg}/" --skip-sbom --confirm
done

echo "==> composing UDS bundle"
uds create infra/uds -o build/ --confirm

echo "==> done:"
ls -lh build/uds-bundle-*.tar.zst
