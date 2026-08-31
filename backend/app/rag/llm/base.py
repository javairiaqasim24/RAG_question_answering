"""Provider-agnostic interface for LLM answer generation."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


class GenerationError(Exception):
    """Raised when an LLM call fails (provider unreachable, model missing, timeout, bad response)."""


@dataclass
class LLMHealth:
    """Cheap reachability/readiness check result, used by GET /health."""

    reachable: bool
    model_available: bool
    error: str | None = None


class LLMProvider(ABC):
    """A backend capable of generating a grounded answer from a system + user prompt."""

    @abstractmethod
    def generate(self, system_prompt: str, user_message: str) -> str:
        """Return the model's answer text. Raises GenerationError on any failure."""

    @abstractmethod
    def check_health(self) -> LLMHealth:
        """Cheaply report whether the provider is reachable and the configured model is ready."""
