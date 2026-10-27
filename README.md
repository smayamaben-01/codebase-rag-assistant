# Codebase Intelligence RAG Assistant

A retrieval-augmented question-answering system over a codebase. Ask "How does dependency injection work?" and it retrieves the relevant functions and classes, then streams back an answer grounded in that code. The indexed codebase is FastAPI's own source (the `fastapi/` package: 48 Python files).

## How it works

```
question
   |
   |--> dense search (Qdrant, all-MiniLM-L6-v2 embeddings) --> top 15 --.
   |                                                                     |--> Reciprocal Rank Fusion --> top 15
   '--> BM25 keyword search (in memory) ---------------------> top 15 --'                                   |
                                                                                  cross-encoder re-ranker --> top 5 chunks
                                                                                                            |
                                                          prompt + chunks --> Ollama (llama3.2:3b) --> streamed answer
```

- **Chunking:** Python's `ast` module splits each file into function and class chunks, keeping name, docstring, file path and start line as metadata. 48 files become 439 chunks. Each chunk is embedded as docstring + code.
- **Retrieval:** dense search (Qdrant, cosine) and BM25 each return their top 15; Reciprocal Rank Fusion (k=60) merges them; a cross-encoder (`ms-marco-MiniLM-L-6-v2`) re-ranks the merged list down to 5.
- **Generation:** the 5 chunks go into a prompt that tells the model to answer only from that code and cite file and function names. Ollama runs `llama3.2:3b` locally and the answer is streamed back.
- **Caching:** Redis stores finished answers (key = normalized question, TTL 1 hour). An answer is written only after the stream completes, so an interrupted request never caches a partial answer.
- **Incremental indexing:** `app/incremental.py` asks git which `fastapi/*.py` files changed since the last indexed commit, deletes those files' points from Qdrant, then re-chunks and re-embeds only them. To try it, first save the commit your index was built from (git -C data/fastapi-src rev-parse HEAD) into app/last_indexed_commit.txt, then run cd app && python incremental.py after pulling new commits into data/fastapi-src.
- **Logging:** structured `key=value` log lines for cache hit/miss, retrieval time, total time, and Ollama token counts and speed. `GET /stats` returns the cache hit rate.
- **Chat page:** a single HTML page served by the app at / streams the answer as it is generated.

## Evaluation

30 hand-written questions, each mapped to the file(s) that should answer it. A retrieved chunk counts as correct if its file is one of the expected files (file-level matching). Top 5 results per question.

- **Precision@5:** fraction of the 5 chunks that come from an expected file
- **Recall:** fraction of the expected files that appear in the top 5
- **MRR:** mean of 1 / (rank of the first correct file)

| Mode | P@5 | Recall | MRR |
|---|---|---|---|
| Dense only | 0.31 | 0.65 | 0.61 |
| BM25 only | 0.36 | 0.67 | 0.64 |
| Hybrid (RRF) | 0.33 | 0.62 | 0.64 |
| Hybrid + re-rank | 0.34 | 0.70 | 0.60 |

Excluding question 4 (CORS), a known edge case: `fastapi/middleware/cors.py` is a one-line re-export of Starlette's `CORSMiddleware`, so it has no functions or classes to chunk.

| Mode | P@5 | Recall | MRR |
|---|---|---|---|
| Dense only | 0.32 | 0.67 | 0.63 |
| BM25 only | 0.37 | 0.69 | 0.67 |
| Hybrid (RRF) | 0.34 | 0.64 | 0.66 |
| Hybrid + re-rank | 0.35 | 0.72 | 0.62 |

**How to read this honestly**

- The four modes land within about 0.05 of each other. With 30 questions, one question flipping from miss to hit moves recall by 0.033, so most of these gaps are within noise.
- BM25 alone is competitive: best precision, tied-best MRR. The questions contain exact identifiers (`APIRouter`, `OAuth2`, `Dependant`) that keyword search handles well.
- Re-ranking gives the best recall but the lowest MRR. Compared with hybrid, it ranked the right file higher on 4 questions, lower on 6, and the same on 20.
- Four questions were missed by every mode (resolving dependencies at request time, the OpenAPI Pydantic models, the security base class, the security utilities). Their answers sit in very long chunks or in tiny single-chunk files.

Reproduce (from the project root, with Qdrant running and the index built):

```bash
python -m app.run_eval          # summary tables
python -m app.eval_diagnostic   # per-question ranks for each mode
```

## Generation speed (CPU-only laptop, no GPU)

Single runs of the same question, so treat these as rough.

| Model | Time for one answer | Grounded in the retrieved code? |
|---|---|---|
| llama3.1:8b | ~412 s | Yes |
| llama3.2:3b | ~230 s | Yes |
| qwen2.5:1.5b | ~63 s | No, gave a generic textbook definition |

I use the 3B model. A cache hit returns in about 0.02 s. In one logged cache miss (a short 45-token answer), reading the 2,050-token prompt took 54 s of the 73 s total, so prompt size matters as much as answer length.

## Quickstart

Requirements: Docker Desktop, [Ollama](https://ollama.com), Git, Python 3.12+. Setup is several steps, not one command: the index is built locally and the model runs on the host.

```bash
# 1. Clone this repo, then the codebase to index
git clone https://github.com/smayamaben-01/codebase-rag-assistant.git
cd codebase-rag-assistant
git clone https://github.com/fastapi/fastapi.git data/fastapi-src
git -C data/fastapi-src checkout a9134f626      # the commit used for the eval

# 2. Pull the local model (Ollama must be running)
ollama pull llama3.2:3b

# 3. Start Qdrant and Redis, then build the index (needs a local Python environment)
docker compose up -d qdrant redis
python -m venv venv
venv\Scripts\activate                           # Windows; use `source venv/bin/activate` elsewhere
pip install -r requirements.txt
cd app && python ingest_ast.py && cd ..

# 4. Start the API
docker compose up --build
```

Then open `http://localhost:8000/` for the chat page (or `/docs` for the API), or:

```bash
curl "http://localhost:8000/query?question=How%20does%20APIRouter%20register%20routes%3F"
```

The first answer takes a few minutes on CPU; asking the same question again is instant.

The app container reaches Ollama on the host through `host.docker.internal`. That works on Docker Desktop (Windows and macOS). On Linux, add `extra_hosts: ["host.docker.internal:host-gateway"]` to the `app` service.

## API

| Endpoint | Purpose |
|---|---|
| `GET /` | chat page |
| `GET /health` | liveness check |
| `GET /query?question=...` | streams a grounded answer as plain text |
| `GET /stats` | cache hits, misses and hit rate |

Configuration is read from the environment, with `localhost` as the default: `QDRANT_HOST`, `REDIS_HOST`, `OLLAMA_HOST`.

## Project layout

```
app/main.py              FastAPI app: /query, /stats, /health, cache and logging
app/rag_pipeline.py      retrieve() with four modes, generate_answer_stream()
app/ast_chunker.py       AST-based chunking
app/ingest_ast.py        builds the Qdrant index
app/incremental.py       git-diff-based incremental re-indexing
app/eval_set.py          the 30 evaluation questions
app/run_eval.py          precision / recall / MRR for each retrieval mode
app/eval_diagnostic.py   per-question breakdown of the eval
app/static/index.html    chat page (single HTML file)
Dockerfile, docker-compose.yml
DECISIONS.md             decisions log with the evidence behind each choice
```

Other scripts in `app/` are standalone experiments from earlier phases.

## Limitations

- **Small, self-written eval.** 30 questions, file-level matching. The first six questions' expected files were checked by hand; the rest were mapped from which files contain relevant chunks. Several questions were written from file names and read like "what is in this file?".
- **AST chunking only captures functions and classes.** 22 of the 48 files produce no chunks (re-exports, constants, package markers), so questions whose answer lives there cannot be answered.
- **Slow generation on CPU.** Minutes per uncached answer. The 3B model sometimes skips file citations and has listed a function name that was not in the retrieved context.
- **Incremental indexing is manual.** It updates Qdrant, but the BM25 index is built in memory at startup, so restart the app afterwards. Cached answers can stay stale for up to an hour.
- **Not hosted.** Generation depends on a local Ollama model, so the deliverable is the Docker Compose setup, not a public URL.
- **Model downloads at container start.** The embedding model and cross-encoder download from Hugging Face the first time a container starts.

## Ideas to try next (untested)

- The embedding model and cross-encoder probably truncate long chunks (limits are around 256 to 512 tokens, chunks are 3,000+ characters); embedding a shorter summary of each chunk, or splitting long functions, might help the misses.
- The cross-encoder is trained on web-search passages, not code. A code-aware reranker could change the MRR result.
- Passing fewer or shorter chunks to the model should cut the prompt-reading time, at some risk to answer quality; the eval can measure that trade-off.
- Score answer faithfulness on a sample of generated answers.