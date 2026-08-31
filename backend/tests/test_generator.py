from unittest.mock import MagicMock, patch

import pytest

from app.rag.generator import NOT_FOUND_PHRASE, generate_answer
from app.rag.llm import GenerationError
from app.rag.retriever import RetrievedChunk


def _chunk(text="Paris is the capital of France.") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c1",
        document_id="d1",
        filename="doc.pdf",
        page_number=1,
        chunk_index=0,
        text=text,
        similarity_score=0.9,
    )


def test_generate_answer_returns_not_found_with_no_chunks():
    answer, grounded = generate_answer("Unanswerable question?", [])
    assert NOT_FOUND_PHRASE in answer
    assert grounded is False


def test_generate_answer_marks_grounded_true_and_passes_retrieved_context():
    with patch("app.rag.generator.get_llm_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.generate.return_value = "Paris is the capital of France [1]."
        mock_get_provider.return_value = mock_provider

        answer, grounded = generate_answer("What is the capital of France?", [_chunk()])

    assert grounded is True
    assert "Paris" in answer

    system_prompt, user_message = mock_provider.generate.call_args[0]
    assert "ONLY using information present" in system_prompt
    assert "Paris is the capital of France." in user_message
    assert "doc.pdf" in user_message
    assert "What is the capital of France?" in user_message


def test_generate_answer_marks_grounded_false_when_model_says_not_found():
    with patch("app.rag.generator.get_llm_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.generate.return_value = NOT_FOUND_PHRASE
        mock_get_provider.return_value = mock_provider

        answer, grounded = generate_answer("Unrelated question?", [_chunk()])

    assert grounded is False


def test_generate_answer_raises_generation_error_when_ollama_unavailable():
    with patch("app.rag.generator.get_llm_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.generate.side_effect = GenerationError(
            "Local LLM service is unavailable. Please make sure Ollama is running."
        )
        mock_get_provider.return_value = mock_provider

        with pytest.raises(GenerationError, match="Ollama is running"):
            generate_answer("What is the capital of France?", [_chunk()])


def test_generate_answer_raises_generation_error_on_empty_response():
    with patch("app.rag.generator.get_llm_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.generate.return_value = ""
        mock_get_provider.return_value = mock_provider

        with pytest.raises(GenerationError, match="empty response"):
            generate_answer("What is the capital of France?", [_chunk()])
