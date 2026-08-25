import logging

import psycopg

logger = logging.getLogger(__name__)

def build_schema(dim: int) -> str:
    return f"""
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id text NOT NULL,
    source text NOT NULL,
    content text NOT NULL,
    corpus_commit text NOT NULL DEFAULT '',
    ingested_at timestamptz NOT NULL DEFAULT now(),
    embedding vector({dim}) NOT NULL
);
CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);
"""


def vector_literal(v: list[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in v) + "]"


class VectorStore:
    def __init__(self, database_url: str, dim: int = 384) -> None:
        self._url = database_url
        self._dim = dim
        self._conn: psycopg.Connection | None = None

    def connect(self) -> None:
        self._conn = psycopg.connect(self._url, autocommit=True)
        self._conn.execute(build_schema(self._dim))

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def ping(self) -> bool:
        if self._conn is None:
            return False
        try:
            self._conn.execute("SELECT 1")
            return True
        except psycopg.Error:
            return False

    def insert_chunks(
        self,
        doc_id: str,
        source: str,
        chunks: list[tuple[str, list[float]]],
        corpus_commit: str,
    ) -> int:
        if self._conn is None:
            raise RuntimeError("vector store not connected")
        with self._conn.cursor() as cur:
            for content, embedding in chunks:
                cur.execute(
                    "INSERT INTO chunks (doc_id, source, content, corpus_commit, embedding)"
                    " VALUES (%s, %s, %s, %s, %s::vector)",
                    (doc_id, source, content, corpus_commit, vector_literal(embedding)),
                )
        logger.info("inserted %d chunks for doc %s", len(chunks), doc_id)
        return len(chunks)
