load('ext://restart_process', 'docker_build_with_restart')

default_registry('localhost:5500')

docker_build_with_restart(
    'bulkhead/ingestion-service',
    'apps/ingestion-service',
    entrypoint='uvicorn --factory ingestion_service.app:create_app --host 0.0.0.0 --port 8001',
    live_update=[
        sync('apps/ingestion-service/src', '/app/src'),
    ],
)
docker_build_with_restart(
    'bulkhead/query-api',
    'apps/query-api',
    entrypoint='uvicorn --factory query_api.app:create_app --host 0.0.0.0 --port 8002',
    live_update=[
        sync('apps/query-api/src', '/app/src'),
    ],
)
docker_build('bulkhead/retrieval-service', 'apps/retrieval-service')

k8s_yaml(local(
    'helm dependency update infra/helm/bulkhead >/dev/null && helm template bulkhead infra/helm/bulkhead -f infra/helm/bulkhead/values.yaml -f infra/helm/bulkhead/values-local.yaml --namespace bulkhead',
))

k8s_yaml([
    'infra/istio/namespace.yaml',
    'infra/istio/peer-authentication.yaml',
    'infra/istio/gateway.yaml',
    'infra/istio/virtualservice-query-api.yaml',
    'infra/istio/virtualservice-ingestion.yaml',
    'infra/istio/destinationrule-query-api.yaml',
])

k8s_resource('query-api', port_forwards=8002)
k8s_resource('ingestion-service', port_forwards=8001)
k8s_resource('retrieval-service', port_forwards=50051)
