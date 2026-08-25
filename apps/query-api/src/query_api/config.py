from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BULKHEAD_QUERY_")

    retrieval_address: str = "localhost:50051"
    top_k: int = 5

    inference_backend: str = "stub"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_timeout_seconds: float = 120.0

    audit_database_url: str = "postgresql://bulkhead:bulkhead@localhost:5432/audit"
