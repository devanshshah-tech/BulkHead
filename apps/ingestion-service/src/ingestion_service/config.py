from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BULKHEAD_INGEST_")

    database_url: str = "postgresql://bulkhead:bulkhead@localhost:5432/vectors"
    audit_database_url: str = "postgresql://bulkhead:bulkhead@localhost:5432/audit"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_bucket: str = "corpus"
    s3_access_key: str = "bulkhead"
    s3_secret_key: str = "bulkhead-secret"

    lakefs_enabled: bool = True
    lakefs_endpoint: str = "http://lakefs:8000"
    lakefs_access_key: str = "bulkhead"
    lakefs_secret_key: str = "bulkhead-dev-password"
    lakefs_repo: str = "corpus"
    lakefs_branch: str = "main"

    embedder_backend: str = "sentence-transformers"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    chunk_size: int = 800
    chunk_overlap: int = 120
