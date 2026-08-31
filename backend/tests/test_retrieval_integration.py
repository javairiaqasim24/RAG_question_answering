"""End-to-end retrieval integration test against a live Postgres+pgvector instance.
Skips gracefully if the database is not reachable (e.g. Docker not running)."""
import uuid

import pytest
from sqlalchemy import text


@pytest.fixture(scope="module")
def db_session():
    try:
        from app.models.database import SessionLocal, engine, init_db

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        init_db()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Postgres not reachable: {exc}")

    session = SessionLocal()
    yield session
    session.close()


def test_retrieval_finds_relevant_chunk_over_irrelevant_ones(db_session):
    try:
        from app.models.db import Chunk, Document
        from app.rag.embeddings import embed_texts
        from app.rag.retriever import retrieve
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"RAG dependencies unavailable: {exc}")

    doc_id = str(uuid.uuid4())
    document = Document(
        id=doc_id,
        filename="integration-test.pdf",
        stored_path="/tmp/integration-test.pdf",
        status="indexed",
        page_count=1,
        chunk_count=2,
    )
    db_session.add(document)

    texts = [
        "The mitochondria is the powerhouse of the cell and generates ATP.",
        "Paris is the capital city of France and home to the Eiffel Tower.",
    ]
    try:
        vectors = embed_texts(texts)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Could not load embedding model: {exc}")

    for i, (t, v) in enumerate(zip(texts, vectors, strict=True)):
        db_session.add(
            Chunk(document_id=doc_id, chunk_index=i, page_number=1, text=t, char_count=len(t), embedding=v)
        )
    db_session.commit()

    try:
        results = retrieve(db_session, question="What is the capital of France?", top_k=1)
        assert len(results) == 1
        assert "Paris" in results[0].text
        assert results[0].similarity_score > 0.1
    finally:
        db_session.delete(document)
        db_session.commit()
