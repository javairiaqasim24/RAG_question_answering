# Evaluation Methodology

## Dataset

`evaluation/datasets/qa_dataset.json` contains 9 manually authored questions
over `sample_docs/rag_primer.pdf`, a 4-page original document written for
this project (so licensing is not a concern and every fact has a known
source page):

- 7 answerable questions, each labeled with the ground-truth page(s) that
  should be retrieved and a manually written expected answer.
- 2 deliberately unanswerable questions (facts absent from the document),
  used to check that the system explicitly declines instead of hallucinating.

This is intentionally small. It is meant to sanity-check the pipeline
end-to-end and support configuration comparisons (chunking, top-K), not to
serve as a statistically powered benchmark — see Limitations below.

## Metrics

**Retrieval** (`evaluation/scripts/metrics.py`), computed by comparing the
page numbers of retrieved chunks against each question's ground-truth pages:

- **Hit Rate@K** — fraction of questions where at least one relevant page
  was retrieved in the top K (for unanswerable questions, a "hit" means
  nothing was incorrectly retrieved as if it were relevant).
- **Recall@K** — fraction of all ground-truth relevant pages that were
  retrieved.
- **Precision@K** — fraction of retrieved pages that were actually relevant.

**Generation**, via an LLM-as-judge (`evaluation/scripts/judge.py`) using the
same local Ollama model (`gemma3:4b`) the app uses for generation, scored
0–1. Using the same small local model as both generator and judge is a
known limitation (see below) — a stronger, independent judge model would be
more reliable, but was out of scope for this local-only setup:

- **Correctness** — does the generated answer convey the same substance as
  the manually written reference answer?
- **Faithfulness / groundedness** — is every claim in the generated answer
  actually supported by the retrieved context, independent of whether it
  matches the reference?
- **Refusal accuracy** — for the unanswerable questions, did the system
  correctly say the information was not found, rather than guessing?

## Running the evaluation

```bash
# 1. Backend + Postgres must be running (see README "Running Locally")
# 2. Generate the sample PDF once (already committed, but regeneratable):
python evaluation/scripts/generate_sample_pdf.py

# 3. Run the harness (uploads the sample doc if not already indexed,
#    sweeps K in {3, 5, 8}, and runs the LLM judge if Ollama + the
#    configured model are reachable)
cd evaluation && pip install -r requirements.txt
python scripts/run_evaluation.py --backend-url http://localhost:8000
```

Results are written to `evaluation/results/results.json` (raw, per-question)
and `evaluation/results/results.md` (summary table). **If Ollama or the
configured model is not available, the generation-quality section is
explicitly marked "not run" rather than populated with invented numbers.**

## Experiments

The harness sweeps `top_k ∈ {3, 5, 8}` for retrieval metrics automatically.
Other parameters — chunk size/overlap (`CHUNK_SIZE`, `CHUNK_OVERLAP`),
embedding model (`EMBEDDING_MODEL`), and LLM model (`LLM_MODEL`) — are set
via environment variables (see `.env.example`); re-running the harness after
changing one of these and diffing `results.md` is the intended workflow for
comparing configurations.

## Limitations of this evaluation

- **Small dataset.** 9 questions over one document cannot support strong
  statistical claims; results should be read as a pipeline sanity check.
- **LLM-as-judge bias.** Automated judges tend to reward fluent, confident
  phrasing and can be fooled by plausible-sounding but unsupported claims.
  The manually written expected answers in the dataset are provided
  precisely so a human can spot-check judge scores against them.
- **Author bias.** The same person who wrote the source document authored
  the questions and page labels, which likely makes retrieval easier than on
  a real, noisier document a user uploads.
- **No adversarial or ambiguous questions.** The dataset does not test
  multi-hop reasoning across chunks, contradictory sources, or ambiguous
  phrasing.
- **Small local judge model.** The LLM-judge uses the same 4B-parameter
  local model as the generator (no larger/independent judge is available
  without external API access), which is more prone to malformed JSON output
  or lenient scoring than a larger, independent judge model would be —
  treat judge scores as directional.
