from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str
    embedding_model: str
    embedding_model_loaded: bool
    llm_provider: str
    llm_model: str
    llm_configured: bool
    llm_status: str
    llm_message: str | None = None


class ErrorResponse(BaseModel):
    detail: str
