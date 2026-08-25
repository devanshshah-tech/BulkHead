#!/usr/bin/env bash
set -euo pipefail

REGISTRY="${REGISTRY:-bulkhead}"
TAG="${TAG:-dev}"

SERVICES=(ingestion-service query-api retrieval-service)

for svc in "${SERVICES[@]}"; do
  echo "==> building ${REGISTRY}/${svc}:${TAG}"
  docker build -t "${REGISTRY}/${svc}:${TAG}" "apps/${svc}"
done

echo "==> done"
