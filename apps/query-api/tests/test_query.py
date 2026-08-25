import grpc
import pytest
from fastapi.testclient import TestClient

from query_api.app import create_app
from query_api.config import Settings
from query_api.inference_client import StubInference
from query_api.schema import Citation

CITATIONS = [
    Citation(
        chunk_id="c1",
        doc_id="d1",
        source="runbook.md",
        content="Bulkhead deploys via a single UDS bundle.",
        score=0.93,
        corpus_commit="commit-abc123",
    ),
    Citation(
        chunk_id="c2",
        doc_id="d1",
        source="runbook.md",
        content="The bundle requires no internet access at deploy time.",
        score=0.88,
        corpus_commit="commit-abc123",
    ),
]


class FakeRetrieval:
    def __init__(self, citations=None, healthy=True) -> None:
        self.citations = citations if citations is not None else CITATIONS
        self._healthy = healthy
        self.calls: list[tuple[str, int, str]] = []

    def retrieve(self, query, top_k, corpus_ref=""):
        self.calls.append((query, top_k, corpus_ref))
        return self.citations[:top_k]

    def healthy(self):
        return self._healthy

    def close(self):
        pass


@pytest.fixture
def retrieval():
    return FakeRetrieval()


@pytest.fixture
def client(retrieval):
    app = create_app(
        settings=Settings(inference_backend="stub"),
        retrieval=retrieval,
        inference=StubInference(),
        audit=None,
        connect_audit=False,
    )
    return TestClient(app)


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200


def test_readyz(client, retrieval):
    assert client.get("/readyz").status_code == 200
    retrieval._healthy = False
    assert client.get("/readyz").status_code == 503


def test_query_returns_grounded_answer_with_citations(client, retrieval):
    resp = client.post("/query", json={"question": "how is bulkhead deployed?", "top_k": 2})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["answer"]
    assert body["model"] == "stub-grounded-0.1"
    assert len(body["citations"]) == 2
    assert body["citations"][0]["source"] == "runbook.md"
    assert body["citations"][0]["corpus_commit"] == "commit-abc123"
    assert retrieval.calls == [("how is bulkhead deployed?", 2, "")]


def test_query_with_no_matches():
    app = create_app(
        settings=Settings(inference_backend="stub"),
        retrieval=FakeRetrieval(citations=[]),
        inference=StubInference(),
        audit=None,
        connect_audit=False,
    )
    client = TestClient(app)
    resp = client.post("/query", json={"question": "anything?", "top_k": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["citations"] == []
    assert "No relevant passages" in body["answer"]


def test_query_validation(client):
    assert client.post("/query", json={"question": ""}).status_code == 422
    assert client.post("/query", json={"question": "q", "top_k": 99}).status_code == 422


def test_query_returns_502_when_retrieval_down():
    class BrokenRetrieval:
        def retrieve(self, query, top_k, corpus_ref=""):
            raise grpc.RpcError("connection refused")

        def healthy(self):
            return False

        def close(self):
            pass

    app = create_app(
        settings=Settings(inference_backend="stub"),
        retrieval=BrokenRetrieval(),
        inference=StubInference(),
        audit=None,
        connect_audit=False,
    )
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/query", json={"question": "hello?"})
    assert resp.status_code == 502


def test_graphql_ask(client):
    query = """
    query {
      ask(question: "how is bulkhead deployed?", topK: 2) {
        answer
        model
        citations { source score corpusCommit }
      }
    }
    """
    resp = client.post("/graphql", json={"query": query})
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]["ask"]
    assert data["answer"]
    assert len(data["citations"]) == 2
    assert data["citations"][0]["source"] == "runbook.md"
    assert data["citations"][0]["corpusCommit"] == "commit-abc123"
