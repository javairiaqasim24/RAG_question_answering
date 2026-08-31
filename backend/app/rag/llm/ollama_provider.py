"""Local Ollama LLM provider — the default and active provider for this project."""
import logging

import httpx

from app.core.config import get_settings
from app.rag.llm.base import GenerationError, LLMHealth, LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    def __init__(self) -> None:
        self.settings = get_settings()

    def generate(self, system_prompt: str, user_message: str) -> str:
        settings = self.settings
        url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
        payload = {
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {"num_predict": settings.llm_max_tokens},
        }

        try:
            response = httpx.post(url, json=payload, timeout=settings.llm_timeout_seconds)
        except httpx.ConnectError as exc:
            raise GenerationError(
                "Local LLM service is unavailable. Please make sure Ollama is running "
                f"at {settings.ollama_base_url}."
            ) from exc
        except httpx.TimeoutException as exc:
            raise GenerationError(
                "The local LLM took too long to respond. Try a shorter question, a "
                "smaller top-K, or increase LLM_TIMEOUT_SECONDS."
            ) from exc
        except httpx.HTTPError as exc:
            raise GenerationError("Could not reach the local LLM service.") from exc

        if response.status_code >= 400:
            detail = self._extract_error(response)
            if response.status_code == 404 or "not found" in detail.lower():
                raise GenerationError(
                    f"Model '{settings.ollama_model}' is not installed in Ollama. Run "
                    f"`ollama pull {settings.ollama_model}` and try again."
                )
            raise GenerationError(f"Local LLM service returned an error: {detail}")

        try:
            body = response.json()
        except ValueError as exc:
            raise GenerationError("Local LLM service returned an unreadable response.") from exc

        answer = (body.get("message") or {}).get("content", "").strip()
        if not answer:
            raise GenerationError("The local LLM returned an empty response.")
        return answer

    def check_health(self) -> LLMHealth:
        settings = self.settings
        url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
        try:
            response = httpx.get(url, timeout=3.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return LLMHealth(
                reachable=False,
                model_available=False,
                error=f"Ollama is not reachable at {settings.ollama_base_url}: {exc}",
            )

        try:
            models = [m.get("name", "") for m in response.json().get("models", [])]
        except ValueError:
            return LLMHealth(reachable=True, model_available=False, error="Could not parse the Ollama model list.")

        target = settings.ollama_model
        target_base = target.split(":")[0]
        model_available = any(m == target or m.split(":")[0] == target_base for m in models)
        error = None
        if not model_available:
            error = f"Model '{target}' is not installed in Ollama. Run `ollama pull {target}`."
        return LLMHealth(reachable=True, model_available=model_available, error=error)

    @staticmethod
    def _extract_error(response: httpx.Response) -> str:
        try:
            return str(response.json().get("error", response.text))
        except ValueError:
            return response.text or f"HTTP {response.status_code}"
