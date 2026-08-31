from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    document_id: str | None = Field(
        default=None, description="Restrict retrieval to a single document, if provided."
    )
    top_k: int | None = Field(default=None, ge=1, le=20)


class RetrievedSource(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: int | None
    chunk_index: int
    text: str
    similarity_score: float


class QueryResponse(BaseModel):
    question: str
    answer: str
    grounded: bool
    sources: list[RetrievedSource]
    model: str
    retrieved_chunk_count: int
