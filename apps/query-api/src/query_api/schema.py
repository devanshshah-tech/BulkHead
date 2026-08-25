from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    corpus_ref: str = ""


class Citation(BaseModel):
    chunk_id: str
    doc_id: str
    source: str
    content: str
    score: float
    corpus_commit: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    model: str
    corpus_ref: str
