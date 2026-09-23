from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from .rag_pipeline import retrieve, generate_answer_stream
import time

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/query")
def query(question: str):
    t0 = time.time()
    top_chunks = retrieve(question)
    t1 = time.time()
    print(f"Retrieval took: {t1 - t0:.2f}s")
    print(f"Using model: llama3.2:3b")  # update this line manually whenever you swap models

    def timed_stream():
        yield from generate_answer_stream(question, top_chunks)
        print(f"Total (including generation): {time.time() - t0:.2f}s")
        

    return StreamingResponse(timed_stream(), media_type="text/plain")

