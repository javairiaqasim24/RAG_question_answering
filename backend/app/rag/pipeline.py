"""End-to-end document ingestion pipeline: parse -> clean -> chunk -> embed -> store."""
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ingestion.chunker import chunk_pages
from app.ingestion.cleaner import clean_text
from app.ingestion.pdf_parser import PDFExtractionError, extract_pages
from app.models.db import Chunk, Document
from app.rag.embeddings import embed_texts

logger = logging.getLogger(__name__)
settings = get_settings()


def process_document(db: Session, document: Document, file_path: Path) -> None:
    """Run the full ingestion pipeline for a single document, updating its status.

    On any failure, marks the document as 'failed' with an error message rather
    than raising, so the upload endpoint can report a clean per-document status.
    """
    try:
        pages = extract_pages(file_path)
        cleaned_pages = [(p.page_number, clean_text(p.text)) for p in pages]
        raw_chunks = chunk_pages(cleaned_pages, settings.chunk_size, settings.chunk_overlap)

        if not raw_chunks:
            raise PDFExtractionError("Document produced no usable text chunks after cleaning.")

        embeddings = embed_texts([c.text for c in raw_chunks])

        for idx, (chunk, vector) in enumerate(zip(raw_chunks, embeddings, strict=True)):
            db.add(
                Chunk(
                    document_id=document.id,
                    chunk_index=idx,
                    page_number=chunk.page_number,
                    text=chunk.text,
                    char_count=len(chunk.text),
                    embedding=vector,
                )
            )

        document.page_count = len(pages)
        document.chunk_count = len(raw_chunks)
        document.status = "indexed"
        document.error_message = None

    except PDFExtractionError as exc:
        logger.warning("PDF extraction failed for %s: %s", document.filename, exc)
        document.status = "failed"
        document.error_message = str(exc)
    except Exception as exc:  # noqa: BLE001 — convert any unexpected failure into a safe status
        logger.exception("Unexpected ingestion failure for %s", document.filename)
        document.status = "failed"
        document.error_message = "An unexpected error occurred while processing this document."

    db.add(document)
    db.commit()
