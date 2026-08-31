"""LLM answer generation grounded in retrieved context, via a pluggable LLM provider
(default: local Ollama running gemma3:4b — see app/rag/llm/)."""
import logging

from app.rag.llm import GenerationError, get_llm_provider
from app.rag.retriever import RetrievedChunk

logger = logging.getLogger(__name__)

NOT_FOUND_PHRASE = "The information was not found in the uploaded documents."

SYSTEM_PROMPT = f"""You are an academic research assistant that answers questions \
strictly using the provided document excerpts. The excerpts were retrieved from \
documents the user uploaded, via vector similarity search.

Rules:
1. Answer ONLY using information present in the numbered context excerpts below. \
Do not use outside knowledge and do not speculate.
2. Do not invent facts, statistics, or citations that are not directly supported \
by the context.
3. If the context does not contain enough information to answer the question, \
respond with exactly this sentence, verbatim, as the first line of your answer: \
"{NOT_FOUND_PHRASE}" — you may add one short sentence after it describing what \
the documents do cover, if relevant.
4. When you can answer, be clear, direct, and refer to supporting excerpts by \
their bracketed number (e.g. [1], [2]) matching the Context section.
5. Preserve important numbers, names, dates, and technical details from the \
source excerpts exactly as written.
6. Keep answers concise — a few sentences to a short paragraph, unless the \
question requires more detail."""


def _build_context_block(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        page = f", page {chunk.page_number}" if chunk.page_number else ""
        parts.append(f"[{i}] Source: {chunk.filename}{page}\n{chunk.text}")
    return "\n\n---\n\n".join(parts)


def generate_answer(question: str, chunks: list[RetrievedChunk]) -> tuple[str, bool]:
    """Generate a grounded answer from retrieved chunks.

    Returns (answer_text, grounded) where grounded is False when the model
    indicates the answer was not found in the retrieved context.
    """
    if not chunks:
        return NOT_FOUND_PHRASE + " No relevant content was retrieved for this question.", False

    context_block = _build_context_block(chunks)
    user_message = (
        f"Context excerpts from the uploaded documents:\n\n{context_block}\n\n"
        f"---\n\nQuestion: {question}"
    )

    provider = get_llm_provider()
    answer_text = provider.generate(SYSTEM_PROMPT, user_message).strip()
    if not answer_text:
        raise GenerationError("The LLM returned an empty response.")

    grounded = NOT_FOUND_PHRASE.lower() not in answer_text.lower()
    return answer_text, grounded
