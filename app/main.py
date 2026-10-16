from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from .rag_pipeline import retrieve, generate_answer_stream
import time
import redis
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

for noisy in ("httpx", "huggingface_hub", "sentence_transformers"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

logger = logging.getLogger("rag")

app = FastAPI()

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/stats")
def stats():
    hits_raw = r.get("stats:hits")
    misses_raw = r.get("stats:misses")
    
    # Handle None (missing counter) and string conversion from Redis decode_responses=True
    hits = int(hits_raw) if hits_raw is not None else 0
    misses = int(misses_raw) if misses_raw is not None else 0
    
    total = hits + misses
    hit_rate = (hits / total) if total > 0 else 0.0
    
    return {
        "hits": hits,
        "misses": misses,
        "hit_rate": hit_rate
    }

@app.get("/query")
def query(question: str):
    t0 = time.time()
    key = f"query:{question.strip().lower()}"
    cached_response = r.get(key)

    if cached_response is not None:
        r.incr("stats:hits")
        logger.info("cache=%s total_s=%.2f question=%r", "HIT", time.time() - t0, question)

        def cached_generator():
            yield cached_response

        return StreamingResponse(cached_generator(), media_type="text/plain")

    r.incr("stats:misses")
    logger.info("cache=%s question=%r", "MISS", question)
    top_chunks = retrieve(question)
    logger.info("cache=MISS retrieval_s=%.2f model=%s", time.time() - t0, "llama3.2:3b") # update manually when you swap models

    def wrapper():
        pieces = []
        for piece in generate_answer_stream(question, top_chunks):
            pieces.append(piece)
            yield piece  # user sees it immediately
        # only runs after the stream completes fully
        r.set(key, "".join(pieces), ex=3600)
        logger.info("cache=MISS total_s=%.2f model=%s", time.time() - t0, "llama3.2:3b")

    return StreamingResponse(wrapper(), media_type="text/plain")