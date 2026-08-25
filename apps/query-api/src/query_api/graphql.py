import strawberry
from strawberry.fastapi import GraphQLRouter

from .schema import QueryRequest
from .service import QueryService


@strawberry.type
class GCitation:
    chunk_id: str
    doc_id: str
    source: str
    content: str
    score: float
    corpus_commit: str


@strawberry.type
class GAnswer:
    answer: str
    citations: list[GCitation]
    model: str


@strawberry.type
class GQuery:
    @strawberry.field
    def ask(self, info: strawberry.types.Info, question: str, top_k: int = 5) -> GAnswer:
        service: QueryService = info.context["service"]
        result = service.run(QueryRequest(question=question, top_k=top_k))
        return GAnswer(
            answer=result.answer,
            citations=[
                GCitation(
                    chunk_id=c.chunk_id,
                    doc_id=c.doc_id,
                    source=c.source,
                    content=c.content,
                    score=c.score,
                    corpus_commit=c.corpus_commit,
                )
                for c in result.citations
            ],
            model=result.model,
        )


def build_graphql_router(service: QueryService) -> GraphQLRouter:
    schema = strawberry.Schema(query=GQuery)

    def get_context() -> dict:
        return {"service": service}

    return GraphQLRouter(schema, context_getter=get_context)
