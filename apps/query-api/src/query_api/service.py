import time

from .audit import AuditLog
from .inference_client import InferenceClient
from .prompts import build_prompt
from .retrieval_client import RetrievalClient
from .schema import QueryRequest, QueryResponse


class QueryService:
    def __init__(
        self,
        retrieval: RetrievalClient,
        inference: InferenceClient,
        audit: AuditLog | None = None,
    ) -> None:
        self.retrieval = retrieval
        self.inference = inference
        self.audit = audit

    def run(self, req: QueryRequest) -> QueryResponse:
        started = time.monotonic()
        citations = self.retrieval.retrieve(req.question, req.top_k, req.corpus_ref)
        if not citations:
            answer = "No relevant passages were found in the indexed corpus."
        else:
            answer = self.inference.generate(build_prompt(req.question, citations))
        latency_ms = int((time.monotonic() - started) * 1000)

        if self.audit is not None:
            self.audit.record_query(req.question, len(citations), self.inference.model, latency_ms)

        effective_corpus_ref = req.corpus_ref or (citations[0].corpus_commit if citations else "")

        return QueryResponse(
            answer=answer,
            citations=citations,
            model=self.inference.model,
            corpus_ref=effective_corpus_ref,
        )
