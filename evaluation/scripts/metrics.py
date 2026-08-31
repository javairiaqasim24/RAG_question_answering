"""Retrieval and answer-quality metrics for the RAG evaluation harness."""
from dataclasses import dataclass


def hit_at_k(retrieved_pages: list[int], relevant_pages: list[int]) -> bool:
    """True if at least one relevant page appears among the retrieved pages."""
    if not relevant_pages:
        return len(retrieved_pages) == 0  # unanswerable question: a "hit" is retrieving nothing relevant
    return any(p in relevant_pages for p in retrieved_pages)


def recall_at_k(retrieved_pages: list[int], relevant_pages: list[int]) -> float | None:
    """Fraction of all relevant pages that were retrieved. None for unanswerable questions."""
    if not relevant_pages:
        return None
    retrieved_set = set(retrieved_pages)
    hits = sum(1 for p in set(relevant_pages) if p in retrieved_set)
    return hits / len(set(relevant_pages))


def precision_at_k(retrieved_pages: list[int], relevant_pages: list[int]) -> float | None:
    """Fraction of retrieved pages that were actually relevant. None if nothing was retrieved."""
    if not retrieved_pages:
        return None
    relevant_set = set(relevant_pages)
    hits = sum(1 for p in retrieved_pages if p in relevant_set)
    return hits / len(retrieved_pages)


@dataclass
class AggregateRetrievalMetrics:
    hit_rate: float
    mean_recall: float
    mean_precision: float
    n: int


def aggregate_retrieval_metrics(
    per_question_hits: list[bool],
    per_question_recall: list[float | None],
    per_question_precision: list[float | None],
) -> AggregateRetrievalMetrics:
    n = len(per_question_hits)
    recalls = [r for r in per_question_recall if r is not None]
    precisions = [p for p in per_question_precision if p is not None]
    return AggregateRetrievalMetrics(
        hit_rate=sum(per_question_hits) / n if n else 0.0,
        mean_recall=sum(recalls) / len(recalls) if recalls else 0.0,
        mean_precision=sum(precisions) / len(precisions) if precisions else 0.0,
        n=n,
    )
