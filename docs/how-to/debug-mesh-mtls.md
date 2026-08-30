# Debug Istio mTLS & Mesh Connectivity

BulkHead enforces zero-trust communication across all services using Istio with strict mutual TLS (`PeerAuthentication: STRICT`). This guide shows how to inspect certificates, verify mTLS enforcement, and troubleshoot traffic issues within the mesh.

## 1. Verify Strict mTLS Policy

Inspect the `PeerAuthentication` resource in the `bulkhead` namespace:

```bash
kubectl -n bulkhead get peerauthentication -o yaml
```

Ensure `mtls.mode` is set to `STRICT`:

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: bulkhead
spec:
  mtls:
    mode: STRICT
```

## 2. Verify Envoy Sidecar Injection

Every application pod in the `bulkhead` namespace must have an `istio-proxy` sidecar container injected:

```bash
kubectl -n bulkhead get pods -l istio.io/rev=default
```

Inspect the container statuses of a pod:

```bash
kubectl -n bulkhead get pod -l app.kubernetes.io/name=query-api -o jsonpath='{.items[*].spec.containers[*].name}'
# Expected output: query-api istio-proxy
```

## 3. Check mTLS Status via `istioctl`

If `istioctl` is available on your workstation:

```bash
# Check TLS synchronization between query-api and retrieval-service:
istioctl proxy-status

# Verify TLS connection between services:
istioctl authn tls-check $(kubectl -n bulkhead get pod -l app.kubernetes.io/name=query-api -o jsonpath='{.items[0].metadata.name}') retrieval-service.bulkhead.svc.cluster.local
```

## 4. Test Strict Enforcement (Non-Mesh Rejection)

To confirm that non-mTLS plain-text traffic is rejected, spin up a temporary pod **without** Istio sidecar injection and attempt to call the internal retrieval service:

```bash
kubectl run test-unauthenticated --rm -i --tty \
  --image=curlimages/curl \
  --restart=Never \
  --labels="sidecar.istio.io/inject=false" \
  -- curl -v http://retrieval-service.bulkhead.svc.cluster.local:50051
```

**Expected behavior:** The connection is immediately reset or dropped with `Recv failure: Connection reset by peer` / `command terminated with exit code 56` because the client cannot negotiate the mTLS handshake with Envoy.

## 5. Inspect Envoy Access Logs

To view real-time proxy traffic and handshake statuses:

```bash
kubectl -n bulkhead logs -l app.kubernetes.io/name=query-api -c istio-proxy --tail=50 -f
```

Look for HTTP status codes, upstream cluster names, and TLS flags:
- `upstream_cluster`: `outbound|50051||retrieval-service.bulkhead.svc.cluster.local`
- `response_flags`: `-` (healthy) or `UF` (upstream connection failure), `NR` (no route).
