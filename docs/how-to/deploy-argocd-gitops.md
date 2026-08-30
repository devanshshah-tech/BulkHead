# Deploy and Reconcile with ArgoCD GitOps

BulkHead follows the **App-of-Apps** pattern for GitOps-driven delivery in connected environments. All Kubernetes manifests, Helm values, and service deployments are declaratively managed from the `gitops/argocd` directory.

## 1. Directory Structure

```
gitops/argocd/
├── root-app.yaml               # Root Application deploying child applications
└── apps/
    ├── mesh.yaml               # Istio base, istiod, gateways
    ├── data.yaml               # PostgreSQL/pgvector, MinIO, lakeFS
    ├── inference.yaml          # Local Ollama inference deployment
    └── services.yaml           # Ingestion, retrieval, and query-api services
```

## 2. Installing ArgoCD

If deploying to a fresh cluster:

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

## 3. Applying the Root Application

Apply the root application manifest to initiate automatic reconciliation:

```bash
kubectl apply -f gitops/argocd/root-app.yaml
```

ArgoCD will automatically discover and synchronize the child applications defined under `gitops/argocd/apps/`.

## 4. Monitoring Sync Status

Check the status of all BulkHead applications:

```bash
kubectl -n argocd get applications
```

Sample output:

```
NAME                    SYNC STATUS   HEALTH STATUS
bulkhead-root           Synced        Healthy
bulkhead-mesh           Synced        Healthy
bulkhead-data           Synced        Healthy
bulkhead-inference      Synced        Healthy
bulkhead-services       Synced        Healthy
```

## 5. Automated GitOps Drift Detection

When changes are committed to the `main` branch:
1. ArgoCD detects configuration drift against target Helm charts.
2. Changes are automatically reconciled within the cluster.
3. Health probes (`/healthz` and `/readyz`) ensure zero-downtime updates across the RAG microservices.
