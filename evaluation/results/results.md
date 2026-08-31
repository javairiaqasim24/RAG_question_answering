# RAG Evaluation Results

Generated: 2026-08-21 02:19:53

## Retrieval (across top-K experiments)

| K | Hit Rate@K | Recall@K | Precision@K |
|---|-----------:|---------:|------------:|
| 3 | 77.8% | 100.0% | 51.9% |
| 5 | 77.8% | 100.0% | 33.3% |
| 8 | 77.8% | 100.0% | 25.0% |

## Generation Quality

| Metric | Result (K=5) |
|---|---:|
| Answer Correctness | 100.0% |
| Faithfulness | 100.0% |
| Refusal Accuracy (unanswerable Qs) | 100.0% |

_2 of 9 questions failed to generate an answer (e.g. CPU-only inference timeout) and were excluded from the averages above rather than silently dropped — see `per_question` in results.json._

## Limitations

- The evaluation set is small (9 questions over a single 4-page document) and manually authored; it is meant to sanity-check the pipeline, not to be a statistically powered benchmark.
- Correctness/faithfulness scores (when present) come from an LLM judge, which has known biases (e.g. rewarding fluent phrasing) and should be read as directional, not exact.
- Page-level relevance labels were assigned by the same author who wrote the source document, which may make retrieval easier than on a real, messier document.