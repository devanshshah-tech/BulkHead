import pytest
from fastapi.testclient import TestClient

from ingestion_service.app import create_app
from ingestion_service.config import Settings
from ingestion_service.embeddings import HashEmbedder


class FakeVectorStore:
    def __init__(self) -> None:
        self.connected = False
        self.inserted: list[tuple[str, str, int]] = []
        self.healthy = True

    def connect(self) -> None:
        self.connected = True

    def close(self) -> None:
        self.connected = False

    def ping(self) -> bool:
        return self.healthy

    def insert_chunks(self, doc_id, source, chunks, corpus_commit):
        self.inserted.append((doc_id, source, len(chunks)))
        return len(chunks)


class FakeObjectStore:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def ensure_bucket(self) -> None:
        pass

    def put(self, key, data, content_type="application/octet-stream") -> None:
        self.objects[key] = data


class FakeVersioner:
    def commit(self, key, data, metadata):
        return "commit-abc123"


class FakeAudit:
    def __init__(self) -> None:
        self.events: list[tuple] = []

    def connect(self) -> None:
        pass

    def close(self) -> None:
        pass

    def record_ingest(self, doc_id, source, chunks, corpus_commit) -> None:
        self.events.append((doc_id, source, chunks, corpus_commit))


@pytest.fixture
def deps():
    return {
        "settings": Settings(embedder_backend="hash", chunk_size=50, chunk_overlap=10),
        "embedder": HashEmbedder(dim=64),
        "vectors": FakeVectorStore(),
        "objects": FakeObjectStore(),
        "corpus": FakeVersioner(),
        "audit": FakeAudit(),
    }


@pytest.fixture
def client(deps):
    with TestClient(create_app(**deps)) as c:
        yield c


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_readyz(client, deps):
    assert client.get("/readyz").status_code == 200
    deps["vectors"].healthy = False
    assert client.get("/readyz").status_code == 503


def test_ingest_end_to_end(client, deps):
    text = "Bulkhead ships a full RAG stack into disconnected clusters. " * 10
    resp = client.post("/ingest", files={"file": ("notes.txt", text.encode(), "text/plain")})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["source"] == "notes.txt"
    assert body["chunks"] > 1
    assert body["corpus_commit"] == "commit-abc123"
    assert body["embedding_dim"] == 64

    assert deps["vectors"].inserted == [(body["doc_id"], "notes.txt", body["chunks"])]
    assert len(deps["objects"].objects) == 1
    assert deps["audit"].events[0][0] == body["doc_id"]
    assert deps["audit"].events[0][2] == body["chunks"]


def test_ingest_empty_upload(client):
    resp = client.post("/ingest", files={"file": ("empty.txt", b"", "text/plain")})
    assert resp.status_code == 400


def test_internal_embeddings_endpoint(client):
    resp = client.post("/internal/embeddings", json={"texts": ["hello", "world"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["dim"] == 64
    assert len(body["vectors"]) == 2
    assert all(len(v) == 64 for v in body["vectors"])


def test_internal_embeddings_rejects_empty(client):
    assert client.post("/internal/embeddings", json={"texts": []}).status_code == 400
