import re
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
from qdrant_client import QdrantClient
import os
from ast_chunker import extract_chunks

folder = "../data/fastapi-src/fastapi"
all_chunks = []
for root, dirs, files in os.walk(folder):
    for filename in files:
        if filename.endswith(".py"):
            all_chunks.extend(extract_chunks(os.path.join(root, filename)))

STOPWORDS = {"how", "does", "do", "is", "are", "the", "a", "an", "what", "why", "when", "work", "works"}
def tokenize(text):
    words = re.findall(r'\w+', text.lower())
    return [w for w in words if w not in STOPWORDS]

tokenized_corpus = [tokenize(chunk["code"]) for chunk in all_chunks]
bm25 = BM25Okapi(tokenized_corpus)

# Lookup: (file_path, name, start_line) -> full chunk dict
chunk_lookup = {(c["file_path"], c["name"], c["start_line"]): c for c in all_chunks}

model = SentenceTransformer('all-MiniLM-L6-v2')
client = QdrantClient(host="localhost", port=6333)
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

question = "How does dependency injection work?"

# Dense (top 15)
question_vector = model.encode(question)
dense_results = client.query_points(
    collection_name="codebase_chunks", query=question_vector.tolist(), limit=15
).points
dense_ranked = [(r.payload["file_path"], r.payload["name"], r.payload["start_line"]) for r in dense_results]

# BM25 (top 15)
tokenized_query = tokenize(question)
scores = bm25.get_scores(tokenized_query)
top_bm25_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:15]
bm25_ranked = [(all_chunks[i]["file_path"], all_chunks[i]["name"], all_chunks[i]["start_line"]) for i in top_bm25_indices]

# RRF merge
k = 60
rrf_scores = {}
for rank, key in enumerate(dense_ranked, start=1):
    rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (k + rank)
for rank, key in enumerate(bm25_ranked, start=1):
    rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (k + rank)

hybrid_top15 = [key for key, _ in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:15]]

# Re-rank with cross-encoder
candidates = [chunk_lookup[key] for key in hybrid_top15]
pairs = [(question, c["docstring"] + "\n" + c["code"]) for c in candidates]
rerank_scores = reranker.predict(pairs)

reranked = sorted(zip(candidates, rerank_scores), key=lambda x: x[1], reverse=True)[:5]

print("=== Final top 5 after re-ranking ===")
for chunk, score in reranked:
    print(round(score, 3), "-", chunk["file_path"], "-", chunk["name"])

for chunk, score in reranked[:2]:
    print(f"--- {chunk['name']} ---")
    print(chunk['docstring'][:300])
    print()

for chunk, score in reranked:
    full_text = chunk["docstring"] + "\n" + chunk["code"]
    print(chunk["name"], "- full text length (chars):", len(full_text))