# Prove the airgap: deploy with no outbound internet

Deploy the platform into a cluster that has **no route to the internet**, and collect evidence for the "prove it's really airgapped" demo.

## Before you start

This wipes and recreates the `airgap-sim` k3d cluster, including any ingested corpus data.

## Run the script

```bash
./hack/deploy-airgap.sh --yes            # native arch bundle in build/
# or point at any downloaded release artifact:
./hack/deploy-airgap.sh --yes ~/Downloads/uds-bundle-bulkhead-rag-arm64-0.1.1.tar.zst
```

What it does:

1. Creates a docker `--internal` network — containers get **no default gateway**
2. Seeds only the four k3s system images; everything else arrives via the bundle
3. Deploys and waits for health

## Collect proof

```bash
# egress is dead (must FAIL):
kubectl -n bulkhead exec deploy/ollama -c ollama -- curl -m 5 -sS https://example.com

# inference is alive:
kubectl -n bulkhead exec deploy/ollama -c ollama -- ollama list

# full RAG loop works:
kubectl -n bulkhead port-forward svc/query-api 8002:8002 &
curl -s -X POST localhost:8002/query -H 'Content-Type: application/json' \
  -d '{"question":"<your question>"}'
```

Screen-record these three commands — that's your Tier 3 demo clip.
