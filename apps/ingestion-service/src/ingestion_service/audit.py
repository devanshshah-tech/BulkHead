import logging

import psycopg

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS ingest_events (
    id bigserial PRIMARY KEY,
    doc_id text NOT NULL,
    source text NOT NULL,
    chunks integer NOT NULL,
    corpus_commit text NOT NULL DEFAULT '',
    recorded_at timestamptz NOT NULL DEFAULT now()
);
"""


class AuditLog:
    def __init__(self, database_url: str) -> None:
        self._url = database_url
        self._conn: psycopg.Connection | None = None

    def _ensure_conn(self) -> None:
        if self._conn is not None:
            try:
                self._conn.execute("SELECT 1")
                return
            except psycopg.Error:
                try:
                    self._conn.close()
                except psycopg.Error:
                    pass
                self._conn = None
        self._conn = psycopg.connect(self._url, autocommit=True)
        self._conn.execute(SCHEMA)

    def connect(self) -> None:
        self._ensure_conn()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def record_ingest(self, doc_id: str, source: str, chunks: int, corpus_commit: str) -> None:
        try:
            self._ensure_conn()
            self._conn.execute(
                "INSERT INTO ingest_events (doc_id, source, chunks, corpus_commit)"
                " VALUES (%s, %s, %s, %s)",
                (doc_id, source, chunks, corpus_commit),
            )
        except psycopg.Error:
            logger.exception("failed to record ingest audit event")
