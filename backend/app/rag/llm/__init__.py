"""LLM provider abstraction for the RAG generation layer.

The retrieval pipeline (embeddings, pgvector, retriever) never depends on
this package or on any specific LLM backend — only app/rag/generator.py
calls get_llm_provider(), so swapping or adding a provider never touches
retrieval code.
"""
from app.core.config import get_settings
from app.rag.llm.base import GenerationError, LLMHealth, LLMProvider
from app.rag.llm.ollama_provider import OllamaProvider

__all__ = ["GenerationError", "LLMHealth", "LLMProvider", "get_llm_provider"]


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider == "ollama":
        return OllamaProvider()
    raise GenerationError(f"Unsupported LLM_PROVIDER configured: '{settings.llm_provider}'.")
