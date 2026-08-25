import logging
import time
import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from .audit import AuditLog
from .chunking import chunk_text
from .config import Settings
from .corpus import CorpusVersioner, create_versioner
from .embeddings import Embedder, create_embedder
from .objectstore import ObjectStore
from .store import VectorStore

logger = logging.getLogger(__name__)


def _connect_with_retry(connect: Callable[[], None], what: str, attempts: int = 30) -> None:
    for attempt in range(1, attempts + 1):
        try:
            connect()
            return
        except Exception:
            if attempt == attempts:
                raise
            logger.warning("%s not ready, retrying (attempt %d/%d)", what, attempt, attempts)
            time.sleep(2)


class IngestResponse(BaseModel):
    doc_id: str
    source: str
    chunks: int
    corpus_commit: str
    embedding_dim: int


class EmbedRequest(BaseModel):
    texts: list[str]


class EmbedResponse(BaseModel):
    vectors: list[list[float]]
    dim: int


def create_app(
    settings: Settings | None = None,
    embedder: Embedder | None = None,
    vectors: VectorStore | None = None,
    objects: ObjectStore | None = None,
    corpus: CorpusVersioner | None = None,
    audit: AuditLog | None = None,
) -> FastAPI:
    settings = settings or Settings()
    embedder = embedder or create_embedder(settings)
    corpus = corpus or create_versioner(settings)
    vectors = vectors or VectorStore(settings.database_url, dim=embedder.dim)
    objects = objects or ObjectStore(
        settings.s3_endpoint_url,
        settings.s3_access_key,
        settings.s3_secret_key,
        settings.s3_bucket,
    )
    audit = audit or AuditLog(settings.audit_database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if vectors is not None:
            _connect_with_retry(vectors.connect, "vector store")
        if objects is not None:
            _connect_with_retry(objects.ensure_bucket, "object store")
        if audit is not None:
            _connect_with_retry(audit.connect, "audit database")
        yield
        if vectors is not None:
            vectors.close()
        if audit is not None:
            audit.close()

    app = FastAPI(title="bulkhead-ingestion-service", lifespan=lifespan)
    app.state.settings = settings
    app.state.embedder = embedder

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz() -> dict[str, str]:
        if vectors is not None and not vectors.ping():
            raise HTTPException(status_code=503, detail="vector store unavailable")
        return {"status": "ready"}

    @app.post("/ingest", response_model=IngestResponse)
    async def ingest(file: UploadFile = File(...)) -> IngestResponse:  # noqa: B008
        if vectors is None:
            raise HTTPException(status_code=503, detail="vector store not configured")
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="empty upload")

        text = data.decode("utf-8", errors="replace")
        doc_id = str(uuid.uuid4())
        source = file.filename or f"{doc_id}.txt"

        if objects is not None:
            objects.put(f"raw/{doc_id}/{source}", data, file.content_type or "text/plain")

        pieces = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        if not pieces:
            raise HTTPException(status_code=422, detail="no indexable text found")

        corpus_commit = ""
        if corpus is not None:
            corpus_commit = corpus.commit(
                f"raw/{doc_id}/{source}", data, {"doc_id": doc_id, "source": source}
            )

        embeddings = embedder.embed(pieces)
        count = vectors.insert_chunks(
            doc_id, source, list(zip(pieces, embeddings, strict=True)), corpus_commit
        )

        if audit is not None:
            audit.record_ingest(doc_id, source, count, corpus_commit)

        return IngestResponse(
            doc_id=doc_id,
            source=source,
            chunks=count,
            corpus_commit=corpus_commit,
            embedding_dim=embedder.dim,
        )

    @app.post("/internal/embeddings", response_model=EmbedResponse)
    def internal_embeddings(req: EmbedRequest) -> EmbedResponse:
        if not req.texts:
            raise HTTPException(status_code=400, detail="texts must not be empty")
        vectors_out = embedder.embed(req.texts)
        return EmbedResponse(vectors=vectors_out, dim=embedder.dim)

    return app
