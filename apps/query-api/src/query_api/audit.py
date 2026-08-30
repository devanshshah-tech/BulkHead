import logging

import psycopg

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS query_events (
    id bigserial PRIMARY KEY,
    question text NOT NULL,
    citations integer NOT NULL,
    model text NOT NULL DEFAULT '',
    latency_ms integer NOT NULL DEFAULT 0,
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

    def record_query(self, question: str, citations: int, model: str, latency_ms: int) -> None:
        try:
            self._ensure_conn()
            self._conn.execute(
                "INSERT INTO query_events (question, citations, model, latency_ms)"
                " VALUES (%s, %s, %s, %s)",
                (question, citations, model, latency_ms),
            )
        except psycopg.Error:
            logger.exception("failed to record query audit event")
