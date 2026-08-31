# Sample Questions for `rag_primer.pdf`

Upload `sample_docs/rag_primer.pdf` and try these in the UI.

## Answerable (grounded in the document)

1. What is Retrieval-Augmented Generation?
2. Where was the idea of RAG first popularized, and by whom?
3. What are the main stages of a RAG pipeline?
4. Why is it important to use the same embedding model for both queries and document chunks?
5. Why does RAG reduce hallucination compared to a standalone LLM?
6. What metrics are used to evaluate a RAG system's retrieval quality?
7. What two properties are typically assessed when evaluating generation quality?

## Not answerable (should trigger the "not found" response)

8. What is the boiling point of liquid nitrogen?
9. Who is the current CEO of the company that wrote this document?

These are the same questions used in `evaluation/datasets/qa_dataset.json`.
