#!/usr/bin/env bash
# Step 7 — one-command demo refresh: provision/refresh OCI infra, then wait for
# ArgoCD to reconcile. Assumes the one-time bootstrap from PHASE5.md steps 4-6
# (k3s install, ArgoCD install, root-app apply, cloudflared service) is done.
set -euo pipefail

cd "$(dirname "$0")/.."

DEMO_URL="${DEMO_URL:-https://demo.bulkhead.cc}"

echo "==> terraform apply"
(
  cd infra/terraform
  terraform apply -auto-approve
)

VM_IP="$(cd infra/terraform && terraform output -raw instance_public_ip)"

echo "==> waiting for SSH on $VM_IP"
until ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "ubuntu@$VM_IP" true 2>/dev/null; do
  sleep 5
done

echo "==> confirming ArgoCD sync"
argocd app wait root --health --timeout 600

echo "==> demo live at $DEMO_URL"
echo "    (set DEMO_URL env or edit this script once your domain is chosen)"
