"""Real (non-mocked) integration test against a locally running Ollama instance.

Skips automatically if Ollama is not reachable or the configured model is not
pulled — this is meant to be run manually when Ollama is available, per the
project's end-to-end verification workflow, not as a hard CI requirement.
"""
import pytest

from app.rag.generator import generate_answer
from app.rag.llm.ollama_provider import OllamaProvider
from app.rag.retriever import RetrievedChunk


@pytest.fixture(scope="module")
def live_provider() -> OllamaProvider:
    provider = OllamaProvider()
    health = provider.check_health()
    if not health.reachable:
        pytest.skip(f"Ollama not reachable: {health.error}")
    if not health.model_available:
        pytest.skip(f"Ollama model not available: {health.error}")
    return provider


def test_live_generate_returns_nonempty_text(live_provider: OllamaProvider):
    answer = live_provider.generate(
        "You are a helpful assistant. Answer in one short sentence.",
        "What is 2 + 2?",
    )
    assert isinstance(answer, str)
    assert len(answer.strip()) > 0


def test_live_generate_answer_is_grounded_in_retrieved_context(live_provider: OllamaProvider):
    chunk = RetrievedChunk(
        chunk_id="c1",
        document_id="d1",
        filename="doc.pdf",
        page_number=1,
        chunk_index=0,
        text="The Mitacs RAG Primer states that the vector database used is PostgreSQL with the pgvector extension.",
        similarity_score=0.95,
    )
    answer, grounded = generate_answer("Which vector database does the system use?", [chunk])
    assert grounded is True
    assert "pgvector" in answer.lower() or "postgres" in answer.lower()


def test_live_generate_answer_refuses_when_context_unrelated(live_provider: OllamaProvider):
    chunk = RetrievedChunk(
        chunk_id="c2",
        document_id="d1",
        filename="doc.pdf",
        page_number=2,
        chunk_index=1,
        text="The Eiffel Tower was completed in 1889 for the World's Fair in Paris.",
        similarity_score=0.4,
    )
    answer, grounded = generate_answer("What is the boiling point of tungsten?", [chunk])
    assert grounded is False
