"""Embedding tests. Downloads the sentence-transformers model on first run,
so these are skipped gracefully if there is no network access."""
import pytest


@pytest.fixture(scope="module")
def embed_fns():
    try:
        from app.rag.embeddings import embed_query, embed_texts
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Embedding dependencies unavailable: {exc}")
    return embed_texts, embed_query


def test_embed_texts_returns_correct_dimensionality(embed_fns):
    embed_texts, _ = embed_fns
    try:
        vectors = embed_texts(["hello world", "retrieval augmented generation"])
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Could not load embedding model (likely offline): {exc}")
    assert len(vectors) == 2
    assert len(vectors[0]) == 384  # all-MiniLM-L6-v2 dimensionality


def test_query_and_document_share_embedding_space(embed_fns):
    embed_texts, embed_query = embed_fns
    try:
        doc_vec = embed_texts(["The Eiffel Tower is located in Paris, France."])[0]
        similar_query_vec = embed_query("Where is the Eiffel Tower?")
        dissimilar_query_vec = embed_query("How do I bake sourdough bread?")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Could not load embedding model (likely offline): {exc}")

    import numpy as np

    def cosine(a, b):
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    sim_related = cosine(doc_vec, similar_query_vec)
    sim_unrelated = cosine(doc_vec, dissimilar_query_vec)
    assert sim_related > sim_unrelated
