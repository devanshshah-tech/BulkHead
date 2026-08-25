#!/usr/bin/env bash
# Full one-shot local deploy WITHOUT Tilt (platform bootstrap + Helm).
# For the dev inner loop, run this once for cluster+Istio, then use
# `mise run dev` (tilt up) which owns image builds and redeploys.
# Do not run both the Helm step and Tilt against the same cluster at once.
set -euo pipefail

cd "$(dirname "$0")/.."

CLUSTER="bulkhead"
NAMESPACE="bulkhead"

if ! k3d cluster list "$CLUSTER" >/dev/null 2>&1; then
  echo "==> creating k3d cluster '$CLUSTER'"
  k3d cluster create --config infra/k3d/cluster-config.yaml
fi
k3d kubeconfig merge "$CLUSTER" --kubeconfig-switch-context

echo "==> installing istio (istiod + ingress gateway)"
istioctl install --set profile=minimal -y
kubectl create namespace istio-ingress --dry-run=client -o yaml | kubectl apply -f -
helm repo add istio https://istio-release.storage.googleapis.com/charts >/dev/null 2>&1 || true
helm repo update istio >/dev/null
helm upgrade --install istio-ingressgateway istio/gateway \
  --namespace istio-ingress --wait

echo "==> preparing namespace"
kubectl apply -f infra/istio/namespace.yaml

echo "==> importing service images into the cluster"
for svc in ingestion-service query-api retrieval-service; do
  k3d image import "bulkhead/${svc}:dev" -c "$CLUSTER"
done

echo "==> deploying umbrella chart"
helm dependency update infra/helm/bulkhead >/dev/null
helm upgrade --install bulkhead infra/helm/bulkhead \
  --namespace "$NAMESPACE" \
  -f infra/helm/bulkhead/values.yaml \
  -f infra/helm/bulkhead/values-local.yaml \
  --wait --timeout 10m

kubectl apply -f infra/istio/peer-authentication.yaml
kubectl apply -f infra/istio/gateway.yaml
kubectl apply -f infra/istio/virtualservice-query-api.yaml
kubectl apply -f infra/istio/virtualservice-ingestion.yaml
kubectl apply -f infra/istio/destinationrule-query-api.yaml

echo "==> done. Gateway reachable at http://localhost:8080 (Host: bulkhead.local)"
