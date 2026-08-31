import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.db import Document
from app.rag.generator import GenerationError, generate_answer
from app.rag.retriever import retrieve
from app.schemas.query import QueryRequest, QueryResponse, RetrievedSource

logger = logging.getLogger(__name__)
router = APIRouter(tags=["query"])
settings = get_settings()


@router.post("/query", response_model=QueryResponse)
def query_documents(payload: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    indexed_count = db.execute(
        select(func.count()).select_from(Document).where(Document.status == "indexed")
    ).scalar_one()

    if indexed_count == 0:
        raise HTTPException(
            status_code=400,
            detail="No indexed documents are available. Upload and process a document first.",
        )

    if payload.document_id:
        document = db.get(Document, payload.document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Specified document not found.")
        if document.status != "indexed":
            raise HTTPException(status_code=400, detail="Specified document is not yet indexed.")

    chunks = retrieve(
        db, question=payload.question, top_k=payload.top_k, document_id=payload.document_id
    )
    chunks = chunks[: settings.max_context_chunks]

    try:
        answer, grounded = generate_answer(payload.question, chunks)
    except GenerationError as exc:
        logger.warning("Generation failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return QueryResponse(
        question=payload.question,
        answer=answer,
        grounded=grounded,
        sources=[
            RetrievedSource(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                filename=c.filename,
                page_number=c.page_number,
                chunk_index=c.chunk_index,
                text=c.text,
                similarity_score=c.similarity_score,
            )
            for c in chunks
        ],
        model=settings.active_model,
        retrieved_chunk_count=len(chunks),
    )
