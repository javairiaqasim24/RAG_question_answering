from app.core.config import Settings


def test_default_llm_provider_is_ollama():
    settings = Settings(_env_file=None)
    assert settings.llm_provider == "ollama"


def test_default_ollama_base_url_and_model():
    settings = Settings(_env_file=None)
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.ollama_model == "gemma3:4b"


def test_active_model_reads_from_ollama_model_setting():
    settings = Settings(_env_file=None, ollama_model="custom-model:latest")
    assert settings.active_model == "custom-model:latest"
