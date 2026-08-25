#!/usr/bin/env bash
# Bootstrap the local dev cluster: k3d + local registry + Istio + namespace.
# App images/deploys are owned by Tilt (`mise run dev`) by default.
# Set APP_DEPLOY=1 to also deploy the full stack via Helm, in the order
# defined by service_registry.yaml (the no-Tilt path).
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$PWD"

CLUSTER="bulkhead"
NAMESPACE="bulkhead"
VALUES="infra/helm/bulkhead/values.yaml"

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

if [[ "${APP_DEPLOY:-0}" != "1" ]]; then
  echo "==> done. Now run: mise run dev  (tilt up)"
  echo "    Or re-run with APP_DEPLOY=1 for a Helm-only deploy."
  exit 0
fi

# --- Helm-only deploy path, ordered by service_registry.yaml ---
REGISTRY="${REGISTRY:-}"
VALUES_EXTRA=()
[[ -f "${VALUES}.local-overrides" ]] && VALUES_EXTRA+=(-f "${VALUES}.local-overrides")

read_registry() {
  # Emit "<chart>|<values>" lines from service_registry.yaml, layers in
  # order, services in order within each layer. Uses PyYAML when available,
  # falls back to a structural regex otherwise.
  python3 - "$1" <<'PY'
import sys
try:
    import yaml
    doc = yaml.safe_load(open(sys.argv[1]))
    for layer in doc["layers"]:
        for svc in layer["services"]:
            print(f"{svc['chart']}|{svc.get('values', '')}")
except ImportError:
    import re
    text = open(sys.argv[1]).read()
    pat = re.compile(
        r"- name:\s*(\S+)\n\s*chart:\s*(\S+)\n(?:\s*values:\s*(\S+)\n)?"
    )
    for m in pat.finditer(text):
        print(f"{m.group(2)}|{m.group(3) or ''}")
PY
}

echo "==> deploying services in service_registry.yaml order (Helm-only path)"
while IFS='|' read -r chart values; do
  [[ -z "$chart" ]] && continue
  name="$(basename "$chart")"
  echo "  -> helm upgrade --install ${name}"
  helm dependency update "$chart" >/dev/null 2>&1 || true
  helm upgrade --install "$name" "$chart" \
    --namespace "$NAMESPACE" \
    ${values:+-f "$values"} \
    ${REGISTRY:+--set "image.repository=${REGISTRY}/${name}"} \
    --wait --timeout 5m
done < <(read_registry service_registry.yaml)

kubectl apply -f infra/istio/peer-authentication.yaml
kubectl apply -f infra/istio/gateway.yaml
kubectl apply -f infra/istio/virtualservice-query-api.yaml
kubectl apply -f infra/istio/virtualservice-ingestion.yaml
kubectl apply -f infra/istio/destinationrule-query-api.yaml

echo "==> done. Gateway at http://localhost:8080 (Host: bulkhead.local)"
