"""RAG evaluation harness — runs against a live backend instance.

Usage:
    python run_evaluation.py [--backend-url http://localhost:8000]

Requires the backend + Postgres to be running and the sample document already
processed (or reachable for upload). Generation-quality metrics (correctness,
faithfulness) additionally require Ollama to be running with the configured
model pulled — both for the backend's own generation and for this script's
LLM judge (judge.py), which calls Ollama directly. If Ollama/the model is
not available, those metrics are reported as "not run", never fabricated.

Retrieval metrics call the retriever directly (in-process, via the backend
package) rather than through POST /query, so they can be measured
independently of whether generation succeeds — evaluating the retrieval
stage in isolation before the end-to-end system is standard practice for
RAG evaluation (see docs/evaluation/evaluation.md). Generation metrics go
through the real POST /query endpoint, exercising the composed system.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_DIR = SCRIPT_DIR.parent
REPO_ROOT = EVAL_DIR.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from metrics import aggregate_retrieval_metrics, hit_at_k, precision_at_k, recall_at_k  # noqa: E402

DATASET_PATH = EVAL_DIR / "datasets" / "qa_dataset.json"
RESULTS_DIR = EVAL_DIR / "results"
SAMPLE_PDF_PATH = REPO_ROOT / "sample_docs" / "rag_primer.pdf"

EXPERIMENT_KS = [3, 5, 8]
DEFAULT_K_FOR_GENERATION = 5


def load_dataset() -> dict:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def ensure_document(client: httpx.Client, filename: str) -> str:
    docs = client.get("/documents").json()["documents"]
    existing = next((d for d in docs if d["filename"] == filename and d["status"] == "indexed"), None)
    if existing:
        return existing["id"]

    if not SAMPLE_PDF_PATH.exists():
        raise SystemExit(
            f"Sample PDF not found at {SAMPLE_PDF_PATH}. Generate it first with "
            f"evaluation/scripts/generate_sample_pdf.py."
        )

    with open(SAMPLE_PDF_PATH, "rb") as f:
        res = client.post("/documents/upload", files={"file": (filename, f, "application/pdf")})
    res.raise_for_status()
    body = res.json()
    if body["document"]["status"] != "indexed":
        raise SystemExit(f"Sample document failed to index: {body['message']}")
    return body["document"]["id"]


def run_retrieval_experiment(dataset: dict, document_id: str, k: int) -> dict:
    """Measure retrieval quality directly via the backend's retriever, independent
    of whether the LLM generation step is configured/available."""
    from app.models.database import SessionLocal
    from app.rag.retriever import retrieve

    hits, recalls, precisions, per_question = [], [], [], []
    db = SessionLocal()

    for item in dataset["items"]:
        results = retrieve(db, question=item["question"], top_k=k, document_id=document_id)
        retrieved_pages = [r.page_number for r in results if r.page_number is not None]

        h = hit_at_k(retrieved_pages, item["relevant_pages"])
        r = recall_at_k(retrieved_pages, item["relevant_pages"])
        p = precision_at_k(retrieved_pages, item["relevant_pages"])
        hits.append(h)
        recalls.append(r)
        precisions.append(p)
        per_question.append(
            {
                "id": item["id"],
                "question": item["question"],
                "answerable": item["answerable"],
                "relevant_pages": item["relevant_pages"],
                "retrieved_pages": retrieved_pages,
                "hit": h,
                "recall": r,
                "precision": p,
            }
        )

    db.close()
    agg = aggregate_retrieval_metrics(hits, recalls, precisions)
    return {
        "k": k,
        "hit_rate": agg.hit_rate,
        "mean_recall": agg.mean_recall,
        "mean_precision": agg.mean_precision,
        "n_questions": agg.n,
        "per_question": per_question,
    }


def run_generation_experiment(client: httpx.Client, dataset: dict, document_id: str, k: int) -> dict | None:
    health = client.get("/health").json()
    if not health.get("llm_configured"):
        return None

    try:
        from judge import judge_answer
    except ImportError as exc:  # httpx not installed for the judge script
        print(f"Judge unavailable: {exc}", file=sys.stderr)
        return None

    per_question = []
    correctness_scores, faithfulness_scores, not_found_correct = [], [], []
    n_failed = 0

    for item in dataset["items"]:
        try:
            res = client.post(
                "/query",
                json={"question": item["question"], "document_id": document_id, "top_k": k},
            )
            res.raise_for_status()
        except httpx.HTTPError as exc:
            # CPU-only local inference has real latency variance; one slow/failed
            # question should be recorded honestly, not crash the whole harness.
            print(f"Generation request failed for question {item['id']!r}: {exc}", file=sys.stderr)
            n_failed += 1
            per_question.append({"id": item["id"], "error": str(exc)})
            continue

        body = res.json()
        context = "\n\n".join(s["text"] for s in body["sources"])

        if item["answerable"]:
            judged = judge_answer(item["question"], item["expected_answer"], context, body["answer"])
            if judged.get("correctness") is not None:
                correctness_scores.append(judged["correctness"])
            if judged.get("faithfulness") is not None:
                faithfulness_scores.append(judged["faithfulness"])
            per_question.append({"id": item["id"], "grounded": body["grounded"], **judged})
        else:
            # For unanswerable questions, correctness = the system correctly refused.
            correctly_refused = not body["grounded"]
            not_found_correct.append(correctly_refused)
            per_question.append(
                {"id": item["id"], "grounded": body["grounded"], "correctly_refused": correctly_refused}
            )

    return {
        "k": k,
        "mean_correctness": sum(correctness_scores) / len(correctness_scores) if correctness_scores else None,
        "mean_faithfulness": sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else None,
        "not_found_accuracy": sum(not_found_correct) / len(not_found_correct) if not_found_correct else None,
        "n_failed": n_failed,
        "per_question": per_question,
    }


def write_markdown_summary(retrieval_results: list[dict], generation_result: dict | None, path: Path) -> None:
    lines = ["# RAG Evaluation Results", ""]
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Retrieval (across top-K experiments)")
    lines.append("")
    lines.append("| K | Hit Rate@K | Recall@K | Precision@K |")
    lines.append("|---|-----------:|---------:|------------:|")
    for r in retrieval_results:
        lines.append(
            f"| {r['k']} | {r['hit_rate']*100:.1f}% | {r['mean_recall']*100:.1f}% | {r['mean_precision']*100:.1f}% |"
        )
    lines.append("")
    lines.append("## Generation Quality")
    lines.append("")
    if generation_result is None:
        lines.append(
            "**Not run.** Ollama and/or the configured model were not available to the backend, "
            "so no LLM calls were made and no correctness/faithfulness scores were fabricated. "
            "Start Ollama (`ollama serve`), run `ollama pull gemma3:4b`, and re-run this script "
            "to populate this section."
        )
    else:
        lines.append(f"| Metric | Result (K={generation_result['k']}) |")
        lines.append("|---|---:|")
        mc = generation_result["mean_correctness"]
        mf = generation_result["mean_faithfulness"]
        nf = generation_result["not_found_accuracy"]
        lines.append(f"| Answer Correctness | {mc*100:.1f}% |" if mc is not None else "| Answer Correctness | n/a |")
        lines.append(f"| Faithfulness | {mf*100:.1f}% |" if mf is not None else "| Faithfulness | n/a |")
        lines.append(
            f"| Refusal Accuracy (unanswerable Qs) | {nf*100:.1f}% |" if nf is not None else "| Refusal Accuracy | n/a |"
        )
        if generation_result.get("n_failed"):
            lines.append("")
            lines.append(
                f"_{generation_result['n_failed']} of {len(generation_result['per_question'])} questions "
                "failed to generate an answer (e.g. CPU-only inference timeout) and were excluded from "
                "the averages above rather than silently dropped — see `per_question` in results.json._"
            )
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append(
        "- The evaluation set is small (9 questions over a single 4-page document) and manually "
        "authored; it is meant to sanity-check the pipeline, not to be a statistically powered benchmark.\n"
        "- Correctness/faithfulness scores (when present) come from an LLM judge, which has known "
        "biases (e.g. rewarding fluent phrasing) and should be read as directional, not exact.\n"
        "- Page-level relevance labels were assigned by the same author who wrote the source "
        "document, which may make retrieval easier than on a real, messier document."
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend-url", default=os.environ.get("BACKEND_URL", "http://localhost:8000"))
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    dataset = load_dataset()

    with httpx.Client(base_url=args.backend_url, timeout=180.0) as client:
        health = client.get("/health")
        health.raise_for_status()
        print(f"Backend health: {health.json()}")

        document_id = ensure_document(client, dataset["document_filename"])
        print(f"Using document_id={document_id}")

        retrieval_results = []
        for k in EXPERIMENT_KS:
            print(f"Running retrieval experiment K={k}...")
            retrieval_results.append(run_retrieval_experiment(dataset, document_id, k))

        print(f"Running generation experiment K={DEFAULT_K_FOR_GENERATION}...")
        generation_result = run_generation_experiment(client, dataset, document_id, DEFAULT_K_FOR_GENERATION)

    full_results = {
        "retrieval_experiments": retrieval_results,
        "generation_experiment": generation_result,
    }
    (RESULTS_DIR / "results.json").write_text(json.dumps(full_results, indent=2), encoding="utf-8")
    write_markdown_summary(retrieval_results, generation_result, RESULTS_DIR / "results.md")
    print(f"\nResults written to {RESULTS_DIR / 'results.json'} and {RESULTS_DIR / 'results.md'}")


if __name__ == "__main__":
    main()
