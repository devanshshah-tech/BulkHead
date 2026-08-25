from contextlib import asynccontextmanager

import grpc
from fastapi import FastAPI, HTTPException

from .audit import AuditLog
from .config import Settings
from .graphql import build_graphql_router
from .inference_client import InferenceClient, create_inference
from .retrieval_client import RetrievalClient
from .schema import QueryRequest, QueryResponse
from .service import QueryService


def create_app(
    settings: Settings | None = None,
    retrieval: RetrievalClient | None = None,
    inference: InferenceClient | None = None,
    audit: AuditLog | None = None,
    connect_audit: bool = True,
) -> FastAPI:
    settings = settings or Settings()
    retrieval = retrieval or RetrievalClient(settings.retrieval_address)
    inference = inference or create_inference(settings)
    service = QueryService(retrieval, inference, audit)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if audit is not None and connect_audit:
            audit.connect()
        yield
        if audit is not None and connect_audit:
            audit.close()

    app = FastAPI(title="bulkhead-query-api", lifespan=lifespan)
    app.state.service = service

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz() -> dict[str, bool]:
        retrieval_ok = retrieval.healthy()
        inference_ok = inference.healthy()
        if not (retrieval_ok and inference_ok):
            raise HTTPException(
                status_code=503,
                detail={"retrieval": retrieval_ok, "inference": inference_ok},
            )
        return {"retrieval": retrieval_ok, "inference": inference_ok}

    @app.post("/query", response_model=QueryResponse)
    def query(req: QueryRequest) -> QueryResponse:
        try:
            return service.run(req)
        except grpc.RpcError as err:
            raise HTTPException(status_code=502, detail="retrieval service unavailable") from err

    app.include_router(build_graphql_router(service), prefix="/graphql")

    return app
