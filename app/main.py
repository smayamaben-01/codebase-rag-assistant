from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from .rag_pipeline import retrieve, generate_answer_stream
import time
import redis
import os

app = FastAPI()

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/query")
def query(question: str):
    key = f"query:{question.strip().lower()}"
    cached_response = r.get(key)

    if cached_response is not None:
        print("Cache HIT")

        def cached_generator():
            yield cached_response

        return StreamingResponse(cached_generator(), media_type="text/plain")

    print("Cache MISS")
    t0 = time.time()
    top_chunks = retrieve(question)
    print(f"Retrieval took: {time.time() - t0:.2f}s")
    print("Using model: llama3.2:3b")  # update manually when you swap models

    def wrapper():
        pieces = []
        for piece in generate_answer_stream(question, top_chunks):
            pieces.append(piece)
            yield piece  # user sees it immediately
        # only runs after the stream completes fully
        r.set(key, "".join(pieces), ex=3600)
        print(f"Total (including generation): {time.time() - t0:.2f}s")

    return StreamingResponse(wrapper(), media_type="text/plain")