import grpc

from bulkhead.retrieval.v1 import retrieval_pb2, retrieval_pb2_grpc

from .schema import Citation


class RetrievalClient:
    def __init__(self, address: str) -> None:
        self._channel = grpc.insecure_channel(address)
        self._stub = retrieval_pb2_grpc.RetrievalServiceStub(self._channel)

    def retrieve(self, query: str, top_k: int, corpus_ref: str = "") -> list[Citation]:
        resp = self._stub.Retrieve(
            retrieval_pb2.RetrieveRequest(query=query, top_k=top_k, corpus_ref=corpus_ref),
            timeout=15,
        )
        return [
            Citation(
                chunk_id=c.chunk_id,
                doc_id=c.doc_id,
                source=c.source,
                content=c.content,
                score=c.score,
                corpus_commit=c.corpus_commit,
            )
            for c in resp.chunks
        ]

    def healthy(self) -> bool:
        try:
            self._stub.Healthz(retrieval_pb2.HealthzRequest(), timeout=3)
            return True
        except grpc.RpcError:
            return False

    def close(self) -> None:
        self._channel.close()
