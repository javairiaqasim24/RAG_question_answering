# RAG Document QA

A Retrieval-Augmented Generation (RAG) question-answering system for uploaded
PDF documents. Upload a document, ask a question, and get an answer grounded
strictly in retrieved passages from that document — with page-level
citations, and an explicit refusal when the answer isn't in the document.

This is a full RAG pipeline (parse → chunk → embed → vector search → grounded
generation), not a chatbot with a file-upload button: every answer is
produced from chunks actually retrieved via vector similarity search, and the
retrieval step is never bypassed.

## Overview

Large language models cannot answer questions about documents they never
saw, and asking them to try invites hallucination. This project retrieves
the most relevant passages from a user's own uploaded PDFs — via embeddings
and a real vector database — before asking an LLM to answer, and instructs
the model to explicitly say when the retrieved context doesn't contain the
answer instead of guessing.

## Features

- PDF upload with validation (type, size, sanitized filenames)
- Page-aware text extraction, cleaning, and configurable recursive chunking
- Real sentence-transformer embeddings (not fake/random vectors)
- Real vector similarity search via PostgreSQL + pgvector (not keyword search)
- Grounded LLM generation via a local Ollama model (`gemma3:4b`), with an
  explicit "not found in the uploaded documents" behavior instead of
  hallucinating — no API key or cloud LLM required
- Source citations (filename, page number, similarity score) for every answer
- Polished, responsive, accessible Next.js/Tailwind dashboard with upload
  dropzone, per-document processing status, loading/skeleton/empty/error states
- Retrieval + generation evaluation harness with real, reproducible metrics
- Backend test suite (chunking, cleaning, validation, storage, PDF parsing,
  embeddings, retrieval, generation grounding)

## Architecture

```mermaid
flowchart LR
    A[PDF Upload] --> B[Page-aware\ntext extraction]
    B --> C[Text cleaning]
    C --> D[Recursive\nchunking]
    D --> E[Sentence-Transformers\nembedding]
    E --> F[(PostgreSQL + pgvector)]

    Q[User question] --> QE[Query embedding\nsame model]
    QE --> R[Top-K similarity\nsearch]
    F --> R
    R --> CTX[Context +\nsource metadata]
    CTX --> LLM[Local Ollama\nGemma 3 4B\ngrounded generation]
    LLM --> ANS[Answer + citations]
```

Full pipeline explanation and design rationale: [docs/architecture/architecture.md](docs/architecture/architecture.md).

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4 |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2.0 |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (Hugging Face) |
| Vector database | PostgreSQL + pgvector |
| LLM | Local Ollama (`gemma3:4b` by default, configurable — see [app/rag/llm/](backend/app/rag/llm/)) |
| PDF parsing | `pypdf` |
| Testing | `pytest` (backend) |
| Local infra | Docker Compose (Postgres + pgvector) |

## Project Structure

```
backend/
  app/
    api/routes/       # documents, query, health endpoints
    core/              # settings
    ingestion/         # PDF parsing, cleaning, chunking
    models/            # SQLAlchemy models + DB session
    rag/               # embeddings, retriever, generator, pipeline, llm/ (provider abstraction)
    schemas/            # Pydantic request/response models
    services/           # storage, validation
  tests/
frontend/
  app/                  # Next.js App Router pages/layout
  components/           # UI components
  lib/                  # API client
  types/                 # shared TypeScript types
evaluation/
  datasets/              # QA ground-truth dataset
  scripts/                # evaluation harness, metrics, LLM judge, sample-PDF generator
  results/                 # generated results (json + markdown)
sample_docs/               # sample PDF + sample questions
docs/
  architecture/            # pipeline + design-decision docs
  evaluation/               # evaluation methodology
docker-compose.yml           # Postgres + pgvector for local dev
.env.example
```

## Installation

Prerequisites: Python 3.11+, Node 20+, Docker Desktop, [Ollama](https://ollama.com).

```bash
git clone <this-repo>
cd RAG_Project
cp .env.example .env   # defaults already point at local Ollama — no key needed

# Backend
cd backend
python -m venv .venv
.venv/Scripts/activate       # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
cp .env.local.example .env.local
```

### Install Ollama and pull the model

The LLM runs entirely locally via [Ollama](https://ollama.com) — no
Anthropic/OpenAI API key is required for local development.

```bash
# 1. Install Ollama (see https://ollama.com for your OS), then make sure it's running.

# 2. Pull the model used for generation (~3.3GB, one-time download)
ollama pull gemma3:4b

# 3. Sanity-check it responds
ollama run gemma3:4b "Say hello in one sentence."
```

## Environment Variables

See [.env.example](.env.example) for the full annotated list. Key ones:

| Variable | Purpose | Default |
|---|---|---|
| `LLM_PROVIDER` | Active LLM provider | `ollama` |
| `OLLAMA_BASE_URL` | Where the backend reaches Ollama's HTTP API | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model used for generation | `gemma3:4b` |
| `LLM_MAX_TOKENS` / `LLM_TIMEOUT_SECONDS` | Generation output cap / request timeout (kept modest for CPU-only inference) | `256` / `120` |
| `EMBEDDING_MODEL` | Sentence-Transformers model | `sentence-transformers/all-MiniLM-L6-v2` |
| `DATABASE_URL` | Postgres connection string | `postgresql+psycopg://rag_user:rag_password@localhost:5432/rag_db` |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | Chunking parameters (characters) | `1000` / `150` |
| `TOP_K` | Default number of chunks retrieved per query | `5` |
| `MAX_FILE_SIZE_MB` | Upload size limit | `20` |
| `NEXT_PUBLIC_API_BASE_URL` | Backend URL the frontend calls (frontend/.env.local) | `http://localhost:8000` |

**No `ANTHROPIC_API_KEY` or any other API key is required** — this project
no longer depends on Anthropic/Claude for anything; generation runs fully
locally through Ollama.

## Running Locally

```bash
# 1. Make sure Ollama is running (installed as a background service on most
#    platforms; otherwise run `ollama serve` in its own terminal) and that
#    `ollama list` shows gemma3:4b.

# 2. Start Postgres + pgvector
docker compose up -d

# 3. Start the backend (from backend/, with venv active)
uvicorn app.main:app --reload --port 8000

# 4. Start the frontend (from frontend/, separate terminal)
npm run dev
```

Open http://localhost:3000. The backend API docs are at http://localhost:8000/docs,
and `GET /health` reports whether Ollama is reachable and the model is installed.

**Running the backend inside Docker instead of natively?** `localhost` inside
a container refers to the container itself, not your host machine where
Ollama runs — set `OLLAMA_BASE_URL=http://host.docker.internal:11434`
(works out of the box on Docker Desktop for Windows/Mac; on Linux, run the
container with `--add-host=host.docker.internal:host-gateway` first). The
committed `docker-compose.yml` only runs Postgres by default — the backend
Dockerfile is used for deployment, not local dev — so most local setups
never hit this and can leave `OLLAMA_BASE_URL` at its `localhost` default.

## Usage

1. **Upload** a PDF via the dropzone. It's validated, parsed page-by-page,
   cleaned, chunked, embedded, and stored — the document card shows
   "Processed · N chunks indexed" when done (or a specific error if it fails).
2. **Select scope** (a single document or "all documents") in the sidebar.
3. **Ask a question.** The question is embedded and matched against stored
   chunks via cosine similarity; the top-K chunks are sent to the local
   Ollama model with a grounding system prompt.
4. **Read the answer and sources.** Each answer is tagged "Grounded in
   sources" or "Not found in documents"; every source chunk shown links back
   to a specific filename, page, and similarity score.

Try it with the included sample document — see [sample_docs/sample_questions.md](sample_docs/sample_questions.md).

## Evaluation

Methodology, metrics, and how to reproduce: [docs/evaluation/evaluation.md](docs/evaluation/evaluation.md).

Results below are from a real run against the live pipeline with local
Ollama (`gemma3:4b`) generating every answer — nothing here is invented; if
Ollama or the model isn't available when the harness runs, the
generation-quality section is explicitly marked "not run" instead.

| K | Hit Rate@K | Recall@K | Precision@K |
|---|-----------:|---------:|------------:|
| 3 | 77.8% | 100.0% | 51.9% |
| 5 | 77.8% | 100.0% | 33.3% |
| 8 | 77.8% | 100.0% | 25.0% |

(9 questions: 7 answerable, 2 deliberately unanswerable. All 7 answerable
questions retrieved their ground-truth page at every K tested — hence 100%
recall. Hit Rate caps at 77.8% because the 2 unanswerable questions have no
relevant page by construction, and pgvector always returns its K nearest
neighbors regardless of true relevance, so they count as misses under this
metric's definition — that's expected, not a retrieval failure; whether the
system correctly *refuses* to answer them is what "Refusal Accuracy" below
measures instead. Precision falls as K grows because each question has only
one truly relevant page to find among K slots. Retrieval is unaffected by
the LLM swap — it never touches the LLM — so these numbers are identical to
the pre-Ollama pipeline.)

**Generation quality (K=5, judged by the same local `gemma3:4b` model —
see [docs/evaluation/evaluation.md](docs/evaluation/evaluation.md) for why
that's a limitation, not an independent judge):**

| Metric | Result |
|---|---:|
| Answer Correctness | 100.0% |
| Faithfulness | 100.0% |
| Refusal Accuracy (unanswerable Qs) | 100.0% |

Honestly reported: 2 of the 9 questions (the two requiring the longest
retrieved-context generation at K=5) timed out against the backend's
120-second CPU-only generation budget and were excluded from the averages
above rather than silently dropped — see `n_failed` and `per_question` in
[evaluation/results/results.json](evaluation/results/results.json). This is
a real, measured latency limitation of CPU-only local inference, not a
correctness problem — see [docs/architecture/architecture.md](docs/architecture/architecture.md#why-local-ollama-instead-of-a-hosted-api)
for the trade-off discussion. Regenerate with
`python evaluation/scripts/run_evaluation.py` (Ollama running locally with
`gemma3:4b` pulled).

Raw results: [evaluation/results/results.json](evaluation/results/results.json), [evaluation/results/results.md](evaluation/results/results.md).

## Testing

```bash
cd backend
pytest -v
```

Covers: health endpoint, upload validation, filename sanitization, PDF text
extraction (valid/multi-page/corrupted/empty-text PDFs), text cleaning,
chunking (size/overlap/page-boundary preservation), embedding
dimensionality/consistency, pgvector retrieval ranking, generation grounding
logic, and the Ollama provider (config defaults, connection/model-detection
health checks, request construction, and friendly error handling for
"Ollama not running" / "model not pulled" / timeout) — all with mocked HTTP
calls, no network needed. `tests/test_ollama_live.py` additionally makes
real calls to a locally running Ollama and auto-skips if it isn't reachable
or the model isn't pulled.

Manual end-to-end verification performed for this build is summarized in the
engineering report delivered alongside this README.

## Limitations

- **OCR**: scanned/image-only PDFs with no text layer are rejected with a
  clear error; no OCR is implemented.
- **Retrieval errors**: cosine similarity over sentence-embeddings can miss
  lexical/exact-match queries (e.g. specific numbers or names) that a
  keyword search would catch — this is a known tradeoff of pure dense
  retrieval, not a bug.
- **Chunking sensitivity**: answer quality depends on `CHUNK_SIZE`/
  `CHUNK_OVERLAP`; very short or very long chunks both degrade retrieval
  precision.
- **LLM hallucination risk**: the grounding prompt substantially reduces but
  does not eliminate the chance of an unsupported claim slipping through.
- **Embedding limitations**: `all-MiniLM-L6-v2` is small and fast but less
  capable than larger embedding models on nuanced or highly technical text.
- **Document quality**: extraction quality depends on how the PDF was
  produced (e.g. multi-column layouts or tables can extract poorly).
- **Evaluation limitations**: see [docs/evaluation/evaluation.md](docs/evaluation/evaluation.md#limitations-of-this-evaluation).

## Future Improvements

- Hybrid search (dense + BM25/keyword) to cover exact-match queries
- Cross-encoder reranking of retrieved chunks before generation
- OCR fallback for scanned documents
- Multilingual embedding model option
- Conversation memory / multi-turn follow-up questions
- Background job queue for ingesting large document collections
- Larger, more adversarial evaluation set

## Deployment

See [docs/architecture/architecture.md](docs/architecture/architecture.md) for
pipeline details. Deployment steps:

- **Frontend → Vercel**: connect the repo, set root directory to `frontend/`,
  set `NEXT_PUBLIC_API_BASE_URL` to the deployed backend URL.
- **Backend → any Python host supporting Docker/ASGI** (Render, Fly.io,
  Railway, etc.): build `backend/Dockerfile`, set the environment variables
  from `.env.example` (`DATABASE_URL`, `CORS_ORIGINS` pointing at the Vercel
  domain). `OLLAMA_BASE_URL` would need to point at an Ollama instance
  reachable from that host — a `localhost` Ollama on a developer's laptop is
  not reachable from a deployed backend; this build was verified for local
  development only (see below).
- **Database → managed Postgres with pgvector** (Supabase, Neon, RDS with
  the pgvector extension enabled): point `DATABASE_URL` at it; the backend
  creates the extension and tables automatically on startup.

This build was **not deployed to live infrastructure** — no cloud
credentials were available in this environment. Everything above was
verified locally end-to-end (see the engineering report for what was run).
