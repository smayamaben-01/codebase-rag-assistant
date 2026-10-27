# Decisions log

Each entry says what was decided, what evidence it rested on, and how strong that evidence is. Where a result was a single query or a single run, it says so.

## 1. Index only the `fastapi/` source folder

Docs, tests and translations would dilute retrieval and slow the first version. The 48 `.py` files under `fastapi/` are the target.

## 2. AST chunking instead of whole-file chunks

- **Baseline:** one chunk per file (not fixed-size windows). Whole files mix many unrelated functions, so each embedding is a blur.
- **Evidence:** for "How does dependency injection work?", the top-3 cosine scores rose from 0.19-0.28 (whole files) to 0.34-0.38 (AST chunks). This was one query. The 30-question eval was only run on the AST index, so there is no measured whole-file baseline across questions.
- **Result:** 48 files became 439 function and class chunks, with name, docstring, file path and start line as metadata.
- **Limitation:** files with no function or class definitions produce zero chunks (22 of 48). `middleware/cors.py` is a one-line re-export of Starlette's `CORSMiddleware`, so the CORS question cannot be answered from the index. It is kept in the eval as a documented edge case and reported both with and without it.

## 3. Hybrid retrieval (dense + BM25, merged with Reciprocal Rank Fusion)

- **Why:** BM25-only and dense-only each failed on the same query. BM25's top hit for "dependency injection" was `_html_safe_json`, because its docstring says "injection" (XSS injection, a different meaning). Dense search ranked the `Depends` chunk third.
- **Bug found along the way:** RRF keyed chunks by (file, name), which merged two different `__init__` methods in `routing.py` and inflated their score. Adding `start_line` to the key fixed it.
- **Eval result:** no clear win. On question 1 ("dependency injection"), dense search found the right file nowhere in the top 5, while BM25 and hybrid found it at rank 2. Across all 30 questions, hybrid P@5 was 0.33 vs 0.31 for dense and 0.36 for BM25, and its recall (0.62) was the lowest of the four modes.
- **Kept** as the first stage because the re-ranker needs a mixed candidate pool, not because it beat BM25 alone.

## 4. Cross-encoder re-ranking as a second stage

- **Single-query observation:** for the dependency-injection question, the re-ranker put `APIKeyHeader` above `Depends`. Both docstrings describe the result as "the dependency result", so this was a defensible ranking, and the generated answer was good. This is an anecdote, not evidence the stage helps.
- **Eval result:** best recall (0.70) and the lowest MRR (0.60). Per question versus hybrid: better on 4, worse on 6, same on 20. It found the right file on three questions hybrid missed entirely (22, 23, 25) and lost one (30).
- **Decision:** keep it as the default because of the recall gain, and state plainly that the ranking effect is mixed.
- **Untested explanations:** the model was trained on web passages, not code; chunks are long enough to be truncated; file-level labels count a legitimately relevant chunk from another file as a miss.

## 5. How the evaluation was built, and what it can and cannot show

- 30 questions, file-level matching, precision@5 / recall / MRR.
- The first six questions' expected files were verified by hand. The rest were mapped from which files had relevant chunks. A few were written from file names and read like "what is in this file?" (22, 27-29).
- Four questions (24, 27, 28, 29) were missed by every mode. The per-question diagnostic showed their expected files are correct, so these are real misses. They were left in, not removed.
- The staged comparison (dense, BM25, hybrid, re-ranked) was run once, after the pipeline was built. Earlier phases only had single-query spot checks.
- With 30 questions, differences under about 0.05 are within noise.

## 6. Local model (Ollama) instead of a paid API

Cost was the constraint, so generation runs locally on a CPU-only laptop.

| Model | One answer | Grounded? |
|---|---|---|
| llama3.1:8b | ~412 s | Yes |
| llama3.2:3b | ~230 s | Yes |
| qwen2.5:1.5b | ~63 s | No: a generic definition of dependency injection, no reference to the retrieved code |

Single runs. The 1.5B model failed the one thing the system exists to do, so I chose the 3B model.

## 7. Where the time goes in one cache miss

A logged miss: retrieval 1.4 s, reading a 2,050-token prompt 54.1 s, generating 45 tokens (7.4 tokens/s) about 6 s, total 72.7 s. About 11 s is unaccounted for and is probably Ollama loading the model after idle (load time is not logged).

One short answer is a single sample. Longer answers spend more time generating. It does show that prompt size is a real cost, and passing fewer or shorter chunks is the obvious lever. That is untested.

## 8. Redis cache

- Key: `query:` + the lowercased, stripped question. TTL: 1 hour.
- The answer is written only after the stream completes, using a wrapper generator that passes each piece to the client and collects it, so an interrupted request never caches a partial answer.
- Repeat of the same question: about 3-4 minutes (173-221 s observed) became about 0.02 s.
- Hit and miss counters are in Redis; `GET /stats` returns them.

## 9. Incremental indexing

- Reads the last indexed commit from a file, runs `git diff --name-only` against HEAD, keeps `fastapi/*.py`, deletes each changed file's points by `file_path` filter, then re-chunks, re-embeds and upserts.
- **Bug 1: duplicate points.** After a test re-index of `routing.py` the collection grew from 439 to 564 points. The original ingestion had stored paths in a different format (`../data/fastapi-src/fastapi\routing.py`) from the one the delete filter used (`fastapi/routing.py`), so the delete matched nothing. Fix: normalize paths once, in the chunker, then rebuild the index. Verified: 439 before and 439 after.
- **Bug 2: unstable IDs.** The first version derived point IDs from Python's built-in `hash()`. String hashes are randomized per process, so the IDs changed between runs. It worked only because old points are deleted first. IDs now come from an md5 of file, name and start line.
- **Limitation:** the BM25 index lives in memory and is built at app startup, so the app needs a restart after an incremental update.

## 10. Not hosting a live demo

Generation depends on a local Ollama model, which free hosting tiers cannot run. The alternative was a paid cloud LLM API, which I decided against. The deliverable is `docker compose up` plus a screen recording.

## 11. Docker notes

- `pywin32` (Windows-only) had been frozen into `requirements.txt` and broke the Linux image build; removed.
- The image build took 10+ minutes: the default Linux PyTorch install pulls GBs of CUDA libraries that a CPU-only setup never uses. A CPU-only PyTorch install would shrink the image; not done.
- The app image copies the code at build time, so code changes need `docker compose up --build`.
- Setup is not one command: the FastAPI repo must be cloned into `data/`, the index built with `ingest_ast.py`, and Ollama run on the host.