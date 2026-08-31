"""Vector similarity retrieval against pgvector."""
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.db import Chunk, Document
from app.rag.embeddings import embed_query

settings = get_settings()


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    filename: str
    page_number: int | None
    chunk_index: int
    text: str
    similarity_score: float


def retrieve(
    db: Session,
    question: str,
    top_k: int | None = None,
    document_id: str | None = None,
) -> list[RetrievedChunk]:
    """Embed the query and return the top-K most similar chunks via pgvector.

    Similarity score is cosine similarity in [-1, 1] (embeddings are
    L2-normalized, so this equals 1 - cosine_distance).
    """
    k = top_k or settings.top_k
    query_vector = embed_query(question)

    distance = Chunk.embedding.cosine_distance(query_vector)
    stmt = (
        select(Chunk, Document, distance.label("distance"))
        .join(Document, Chunk.document_id == Document.id)
        .where(Document.status == "indexed")
        .order_by(distance)
        .limit(k)
    )
    if document_id:
        stmt = stmt.where(Chunk.document_id == document_id)

    rows = db.execute(stmt).all()

    results: list[RetrievedChunk] = []
    for chunk, document, dist in rows:
        similarity = 1.0 - float(dist)
        results.append(
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=document.id,
                filename=document.filename,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                similarity_score=round(similarity, 4),
            )
        )
    return results
