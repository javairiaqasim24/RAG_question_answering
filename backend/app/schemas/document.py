from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    content_type: str
    file_size_bytes: int
    page_count: int
    chunk_count: int
    status: str
    error_message: str | None = None
    uploaded_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    message: str


class ChunkSourceResponse(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: int | None
    chunk_index: int
    text: str


class DocumentSourcesResponse(BaseModel):
    document_id: str
    filename: str
    chunks: list[ChunkSourceResponse]
