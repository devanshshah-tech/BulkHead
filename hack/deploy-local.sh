#!/usr/bin/env bash
# Bootstrap the local dev cluster: k3d + local registry + Istio + namespace.
# App images/deploys are owned by Tilt (`mise run dev`). To deploy WITHOUT
# Tilt, use Helm directly: helm upgrade --install bulkhead infra/helm/bulkhead ...
set -euo pipefail

cd "$(dirname "$0")/.."

CLUSTER="bulkhead"
NAMESPACE="bulkhead"

if ! k3d cluster list "$CLUSTER" >/dev/null 2>&1; then
  echo "==> creating k3d cluster '$CLUSTER' (with local registry)"
  k3d cluster create --config infra/k3d/cluster-config.yaml
fi
k3d kubeconfig merge "$CLUSTER" --kubeconfig-switch-context >/dev/null
kubectl config set-context k3d-bulkhead --namespace="$NAMESPACE"

echo "==> installing istio (istiod + ingress gateway)"
istioctl install --set profile=minimal -y
kubectl create namespace istio-ingress --dry-run=client -o yaml | kubectl apply -f -
helm repo add istio https://istio-release.storage.googleapis.com/charts >/dev/null 2>&1 || true
helm repo update istio >/dev/null
helm upgrade --install istio-ingressgateway istio/gateway \
  --namespace istio-ingress --wait

echo "==> preparing namespace"
kubectl apply -f infra/istio/namespace.yaml

echo "==> done. Now run: mise run dev  (tilt up)"
echo "    Gateway will be reachable at http://localhost:8080 (Host: bulkhead.local)"
