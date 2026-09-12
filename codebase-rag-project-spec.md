# Codebase Intelligence RAG Assistant — Project Spec

**One-liner:** A RAG system over a codebase + its docs that answers "how does X work" / "where is Y implemented" questions with cited code references, built with hybrid retrieval, re-ranking, and a measured evaluation pipeline.

**Status:** Planning
**Target:** SDE placement project (secondary: ML/AI relevance)

---

## 1. Tech Stack (lock these in before generating code)

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI (Python) | async support, SDE-relevant, easy streaming |
| Vector DB | Qdrant (local/docker, or free cloud) | production-associated, hybrid search support built in |
| Keyword search | BM25 (via `rank_bm25` or Qdrant's built-in sparse vectors) | needed for hybrid retrieval |
| Embeddings | `sentence-transformers` (e.g. `bge-small-en` or `all-MiniLM-L6-v2`) or OpenAI/Voyage embeddings | free/local option available if cost matters |
| Re-ranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` (via `sentence-transformers`) | cheap, well-known, easy to justify in interview |
| LLM | Claude or GPT API | fast to integrate, reliable output |
| Chunking | AST-based (Python `ast` module, or `tree-sitter` for multi-language) | code-aware, not naive char-split — key differentiator |
| Cache | Redis | shows systems thinking |
| Eval | RAGAS or a custom scored eval set | shows rigor |
| Deployment | Docker + Railway/Render, or a cloud VM | shows you can ship, not just prototype |
| Frontend (optional) | Simple React/HTML chat UI, or just a clean API + Postman/curl demo | don't over-invest here — backend depth matters more for SDE roles |

**Target repo to index:** /fastapi/ source folder (skip docs/, tests/, translations)

---

## 2. Architecture (build in this order)

```
[Codebase + Docs]
      ↓
[1. Ingestion & Chunking] → AST-aware chunking (functions/classes as units, with file path + docstring as metadata)
      ↓
[2. Embedding + Indexing] → embeddings → Qdrant (dense vectors + BM25 sparse index)
      ↓
[3. Query] → user question
      ↓
[4. Hybrid Retrieval] → dense search + BM25 search → merge (e.g. Reciprocal Rank Fusion)
      ↓
[5. Re-ranking] → cross-encoder scores top-K candidates → picks top-N
      ↓
[6. Generation] → LLM answers using top-N chunks, cites file/function
      ↓
[7. Response] → streamed back to user via FastAPI (SSE)

Parallel: [8. Eval Pipeline] — runs against a fixed Q&A test set, scores retrieval + faithfulness
Parallel: [9. Incremental Indexing] — git diff aware re-indexing on codebase update
```

---

## 3. Component Decisions & Rationale (fill in "Your reasoning" as you build — this is your decisions log)

### 3.1 Chunking Strategy
- **Decision:** AST-based chunking — split by function/class boundaries rather than fixed character windows.
- **Why it matters:** naive chunking cuts functions mid-body, destroying retrieval quality for code. This is your strongest differentiator vs. tutorial-level RAG projects.
- **Alternative considered:** fixed-size sliding window with overlap (simpler, but worse for code semantics — rejected because code isn't prose).
- **Your reasoning (fill in after building):** _________

### 3.2 Retrieval: Hybrid Search
- **Decision:** combine dense vector search (semantic) with BM25 (exact keyword/identifier match), merged via Reciprocal Rank Fusion (RRF).
- **Why it matters:** pure vector search often misses exact function/variable names (embeddings blur exact identifiers); pure keyword search misses semantic questions like "how does auth work." Hybrid covers both.
- **Alternative considered:** vector-only (simpler, but weak on exact-name lookups — common failure mode you can demo).
- **Your reasoning:** _________

### 3.3 Re-ranking
- **Decision:** retrieve top-20 via hybrid search, re-rank with a cross-encoder, keep top-5 for the LLM context.
- **Why it matters:** bi-encoders (used for initial retrieval) are fast but less precise; cross-encoders are slower but far more accurate at judging query-document relevance. Two-stage retrieval is standard in production RAG.
- **Your reasoning:** _________

### 3.4 Incremental Indexing
- **Decision:** on codebase update, diff against last indexed commit (git), re-chunk/re-embed only changed files.
- **Why it matters:** full re-indexing doesn't scale; this shows you thought about the system running over time, not just once.
- **Your reasoning:** _________

### 3.5 Evaluation Pipeline
- **Decision:** build a 30-50 question test set (mix of "where is X implemented" / "how does Y work" / "why does Z happen") with expected source files as ground truth. Measure:
  - Retrieval: precision@k, recall@k (did the right chunk get retrieved?)
  - Generation: faithfulness (RAGAS or manual scoring — does the answer only use retrieved content?)
- **Why it matters:** almost nobody evaluates their RAG project quantitatively. This turns "I built a RAG app" into "I improved retrieval precision from X% to Y% by adding re-ranking" — a measurable, interview-ready result.
- **Your reasoning:** _________

### 3.6 Caching
- **Decision:** cache (query → response) in Redis with a TTL; cache embeddings for unchanged chunks.
- **Why it matters:** reduces latency + LLM cost on repeated queries — a real production concern.
- **Your reasoning:** _________

---

## 4. Build Phases (suggested order — MVP first, then layer in the "hard parts")

- [ ] **Phase 0:** Pick target repo, set up FastAPI skeleton + Qdrant locally (Docker)
- [ ] **Phase 1 (MVP):** Naive chunking → embed → vector search only → LLM answer. Get end-to-end working first.
- [ ] **Phase 2:** Swap in AST-based chunking. Compare retrieval quality before/after (write down what changed).
- [ ] **Phase 3:** Add BM25 + hybrid merge (RRF).
- [ ] **Phase 4:** Add cross-encoder re-ranking.
- [ ] **Phase 5:** Build eval set + run it against each stage above (this is where your "X% improvement" numbers come from).
- [ ] **Phase 6:** Add streaming responses, caching, incremental indexing.
- [ ] **Phase 7:** Dockerize + deploy, add basic logging (latency, tokens used, cache hit rate).
- [ ] **Phase 8:** (Optional, if time) simple frontend or polished API docs (FastAPI's auto Swagger UI counts for a lot here).

**Tip:** Running eval at each phase (3 vs 4 vs 5) is what gives you real numbers to quote in interviews — don't skip this even under time pressure.

---

## 5. Interview-Readiness Checklist
Before you call this "resume-ready," you should be able to explain without notes:
- [ ] Why AST chunking over fixed-size chunking (with a concrete example of what broke with naive chunking)
- [ ] Why hybrid search over vector-only (with an example query that fails on vector-only)
- [ ] What the re-ranker adds and why it's a separate stage from initial retrieval
- [ ] Your eval numbers — at least one "before/after" comparison
- [ ] One thing that didn't work initially and how you debugged it

---

## 6. Decisions Log (add entries as you go)

| Date | Decision | Reasoning | Alternative rejected |
|---|---|---|---|
| 10-08-2026 | Index FastAPI's /fastapi/ source dir only | Full repo (docs+tests+translations) would dilute retrieval relevance and slow MVP | Indexing entire repo |

Naive chunking: scores 0.19-0.28, mostly whole-file dilution. AST chunking: scores 0.34-0.38, but ranking still imperfect — most relevant chunk (Depends class) ranked #3 instead of #1, showing vector-only search's limitation with exact terminology. Motivates Phase 3 hybrid search.

BM25-only: top-ranked chunk was a false positive — 'injection' matched but referred to XSS injection, not dependency injection. Demonstrates BM25's lack of semantic understanding. Motivates RRF merge with dense search.

Hybrid search (dense + BM25 + RRF) eliminated false positives present in BM25-only results (e.g., _html_safe_json). However, RRF alone couldn't fully resolve near-duplicate entities (Depends class vs. Depends function) competing for the same concept — motivating re-ranking in Phase 4, where a cross-encoder can directly compare each candidate against the query for finer-grained relevance judgment.

Cross-encoder re-ranking surfaced APIKeyHeader/APIKeyCookie above Depends itself for 'how does dependency injection work' — investigated and confirmed this isn't a bug: both docstrings explicitly describe themselves as providing 'the dependency result,' making them legitimately relevant, arguably more illustrative examples than Depends's own signature. This highlights a genuine ambiguity in 'relevance' for RAG over code — the most conceptually relevant answer isn't always the definition itself, but sometimes a clear usage example. Also noted: chunks average 3,400-4,000 characters, likely exceeding the cross-encoder's ~512 token limit, though uniformly across candidates so it didn't bias this particular result.

Final pipeline test confirms the re-ranking result from Phase 4 was correct, not a flaw — combining Depends + APIKeyHeader in the prompt let the LLM generate a concrete usage example rather than an abstract definition, producing a more useful answer than pure 'find the Depends definition' retrieval would have.