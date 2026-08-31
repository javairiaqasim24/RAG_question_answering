"""LLM-as-judge for answer correctness and faithfulness, via the same local
Ollama model the app uses for generation.

This is an automated evaluation aid, not a ground-truth oracle: LLM judges
have known biases (e.g. favoring longer or more confident-sounding answers),
and a small local model is less reliable at strict structured-output
instructions than a larger hosted one — its scores should be read alongside
the manually-authored expected answers in qa_dataset.json, not as a
replacement for them. See docs/evaluation/ for a fuller discussion.
"""
import json
import os
import re
import sys

import httpx

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", os.environ.get("OLLAMA_MODEL", "gemma3:4b"))

JUDGE_SYSTEM_PROMPT = """You are a strict evaluator for a Retrieval-Augmented \
Generation system. You will be given a question, a reference (expected) answer, \
the context that was actually retrieved, and the answer the system generated. \
Score two things on a 0-1 scale (1 = fully satisfies, 0 = fails entirely):

- correctness: does the generated answer convey the same substantive information \
as the reference answer?
- faithfulness: is every claim in the generated answer actually supported by the \
retrieved context (regardless of whether it matches the reference answer)?

Respond with ONLY a JSON object, no other text and no markdown code fences: {"correctness": <0-1>, "faithfulness": <0-1>, "reasoning": "<one sentence>"}"""


def _strip_markdown_fence(text: str) -> str:
    """Small local models often wrap JSON in ```json ... ``` despite instructions not to."""
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def judge_answer(
    question: str, expected_answer: str, retrieved_context: str, generated_answer: str
) -> dict:
    user_message = (
        f"Question: {question}\n\n"
        f"Reference answer: {expected_answer}\n\n"
        f"Retrieved context:\n{retrieved_context}\n\n"
        f"Generated answer: {generated_answer}"
    )
    try:
        response = httpx.post(
            f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat",
            json={
                "model": JUDGE_MODEL,
                "messages": [
                    {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
                "options": {"num_predict": 300},
            },
            timeout=120.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        # CPU-only local inference has real latency variance; a slow/failed judge
        # call should be recorded honestly rather than crashing the whole harness.
        print(f"WARNING: judge call failed: {exc}", file=sys.stderr)
        return {"correctness": None, "faithfulness": None, "reasoning": f"judge call failed: {exc}"}

    text = response.json().get("message", {}).get("content", "{}")
    try:
        return json.loads(_strip_markdown_fence(text))
    except json.JSONDecodeError:
        print(f"WARNING: judge returned non-JSON output: {text!r}", file=sys.stderr)
        return {"correctness": None, "faithfulness": None, "reasoning": "judge output unparsable"}
