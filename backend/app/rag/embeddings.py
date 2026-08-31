"""Sentence-Transformers embedding service.

Loaded once as a module-level singleton (the model is ~90MB and expensive to
reload) and reused for both document-chunk embedding at ingestion time and
query embedding at retrieval time, so both live in the same vector space.
"""
import logging
import threading

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_model: SentenceTransformer | None = None
_model_lock = threading.Lock()


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                logger.info("Loading embedding model: %s", settings.embedding_model)
                _model = SentenceTransformer(settings.embedding_model)
    return _model


def is_model_loaded() -> bool:
    return _model is not None


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of chunk texts. Uses the same model/space as embed_query."""
    if not texts:
        return []
    model = get_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    """Embed a single user query into the same vector space as document chunks."""
    model = get_embedding_model()
    vector = model.encode([text], normalize_embeddings=True, show_progress_bar=False)
    return vector[0].tolist()
