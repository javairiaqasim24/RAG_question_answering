import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.db import Chunk, Document
from app.rag.pipeline import process_document
from app.schemas.document import (
    ChunkSourceResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentSourcesResponse,
    DocumentUploadResponse,
)
from app.services import storage
from app.services.validation import ValidationError, validate_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(file: UploadFile, db: Session = Depends(get_db)) -> DocumentUploadResponse:
    content = await file.read()

    try:
        validate_upload(file.filename or "", file.content_type, len(content))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    document_id = storage.new_document_id()

    try:
        stored_path = storage.save_upload(document_id, file.filename or "document.pdf", content)
    except OSError as exc:
        logger.exception("Failed to save uploaded file")
        raise HTTPException(status_code=500, detail="Failed to store uploaded file.") from exc

    document = Document(
        id=document_id,
        filename=storage.sanitize_filename(file.filename or "document.pdf"),
        stored_path=str(stored_path),
        content_type=file.content_type or "application/pdf",
        file_size_bytes=len(content),
        status="processing",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Synchronous ingestion keeps the stack simple (no job queue/worker) and
    # gives the client an immediate, accurate final status. For large batches
    # of very large documents, this would be moved to a background worker.
    process_document(db, document, stored_path)
    db.refresh(document)

    message = (
        f"Document processed successfully: {document.chunk_count} chunks indexed."
        if document.status == "indexed"
        else f"Document processing failed: {document.error_message}"
    )
    return DocumentUploadResponse(document=DocumentResponse.model_validate(document), message=message)


@router.get("", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db)) -> DocumentListResponse:
    documents = db.execute(select(Document).order_by(Document.uploaded_at.desc())).scalars().all()
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents], total=len(documents)
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str, db: Session = Depends(get_db)) -> None:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    db.delete(document)  # cascades to chunks
    db.commit()

    try:
        storage.delete_document_files(document_id)
    except OSError:
        logger.exception("Failed to delete files for document %s", document_id)


@router.get("/{document_id}/sources", response_model=DocumentSourcesResponse)
def get_document_sources(document_id: str, db: Session = Depends(get_db)) -> DocumentSourcesResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    chunks = (
        db.execute(
            select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index)
        )
        .scalars()
        .all()
    )
    return DocumentSourcesResponse(
        document_id=document.id,
        filename=document.filename,
        chunks=[
            ChunkSourceResponse(
                chunk_id=c.id,
                document_id=document.id,
                filename=document.filename,
                page_number=c.page_number,
                chunk_index=c.chunk_index,
                text=c.text,
            )
            for c in chunks
        ],
    )
