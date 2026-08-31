"""Unit tests for OllamaProvider, with the Ollama HTTP API mocked (no network)."""
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.rag.llm.base import GenerationError
from app.rag.llm.ollama_provider import OllamaProvider


def _provider() -> OllamaProvider:
    return OllamaProvider()


def test_generate_returns_message_content_and_sends_system_and_user_messages():
    provider = _provider()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": {"content": "Hello there."}}

    with patch("app.rag.llm.ollama_provider.httpx.post", return_value=mock_response) as mock_post:
        result = provider.generate("system instructions", "user question")

    assert result == "Hello there."
    sent = mock_post.call_args.kwargs["json"]
    assert sent["model"] == provider.settings.ollama_model
    assert sent["messages"][0] == {"role": "system", "content": "system instructions"}
    assert sent["messages"][1] == {"role": "user", "content": "user question"}
    assert sent["stream"] is False


def test_generate_raises_friendly_error_when_ollama_unreachable():
    provider = _provider()
    with patch("app.rag.llm.ollama_provider.httpx.post", side_effect=httpx.ConnectError("boom")):
        with pytest.raises(GenerationError, match="make sure Ollama is running"):
            provider.generate("system", "user question")


def test_generate_raises_friendly_error_on_timeout():
    provider = _provider()
    with patch(
        "app.rag.llm.ollama_provider.httpx.post",
        side_effect=httpx.TimeoutException("timed out"),
    ):
        with pytest.raises(GenerationError, match="took too long"):
            provider.generate("system", "user question")


def test_generate_raises_friendly_error_when_model_missing():
    provider = _provider()
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"error": f"model '{provider.settings.ollama_model}' not found"}
    mock_response.text = ""

    with patch("app.rag.llm.ollama_provider.httpx.post", return_value=mock_response):
        with pytest.raises(GenerationError, match="ollama pull"):
            provider.generate("system", "user question")


def test_generate_raises_on_empty_response():
    provider = _provider()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": {"content": "   "}}

    with patch("app.rag.llm.ollama_provider.httpx.post", return_value=mock_response):
        with pytest.raises(GenerationError, match="empty response"):
            provider.generate("system", "user question")


def test_check_health_reports_ready_when_model_present():
    provider = _provider()
    mock_response = MagicMock()
    mock_response.json.return_value = {"models": [{"name": provider.settings.ollama_model}]}

    with patch("app.rag.llm.ollama_provider.httpx.get", return_value=mock_response):
        health = provider.check_health()

    assert health.reachable is True
    assert health.model_available is True
    assert health.error is None


def test_check_health_reports_model_not_available():
    provider = _provider()
    mock_response = MagicMock()
    mock_response.json.return_value = {"models": [{"name": "llama3:8b"}]}

    with patch("app.rag.llm.ollama_provider.httpx.get", return_value=mock_response):
        health = provider.check_health()

    assert health.reachable is True
    assert health.model_available is False
    assert "ollama pull" in health.error


def test_check_health_reports_unreachable():
    provider = _provider()
    with patch("app.rag.llm.ollama_provider.httpx.get", side_effect=httpx.ConnectError("boom")):
        health = provider.check_health()

    assert health.reachable is False
    assert health.model_available is False
    assert health.error is not None
