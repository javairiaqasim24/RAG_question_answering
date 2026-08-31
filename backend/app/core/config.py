"""Central application configuration, loaded from environment variables / .env."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[REPO_ROOT / ".env", BACKEND_DIR / ".env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM (local Ollama by default — see app/rag/llm/ for the provider abstraction)
    llm_provider: str = "ollama"
    llm_max_tokens: int = 256
    llm_timeout_seconds: float = 120.0
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # Database
    database_url: str = "postgresql+psycopg://rag_user:rag_password@localhost:5432/rag_db"

    # RAG pipeline
    chunk_size: int = 1000
    chunk_overlap: int = 150
    top_k: int = 5
    max_context_chunks: int = 8

    # Uploads
    max_file_size_mb: int = 20
    upload_dir: str = "./data/uploads"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def upload_path(self) -> Path:
        path = (BACKEND_DIR / self.upload_dir).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def active_model(self) -> str:
        """Name of the model actually used for generation, for the currently configured provider."""
        return self.ollama_model


@lru_cache
def get_settings() -> Settings:
    return Settings()
