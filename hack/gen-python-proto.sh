#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/apps/query-api/src"

uv run --directory "$ROOT/apps/query-api" --with grpcio-tools --with grpcio --with protobuf \
  python -m grpc_tools.protoc \
  -I "$ROOT/proto" \
  --python_out="$OUT" \
  --grpc_python_out="$OUT" \
  --pyi_out="$OUT" \
  "$ROOT/proto/bulkhead/retrieval/v1/retrieval.proto"

echo "generated python stubs under $OUT/bulkhead/retrieval/v1"
