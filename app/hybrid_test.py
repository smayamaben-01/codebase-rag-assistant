import re
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import os
from ast_chunker import extract_chunks

# Rebuild chunk list + BM25 index
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

# Dense setup
model = SentenceTransformer('all-MiniLM-L6-v2')
client = QdrantClient(host="localhost", port=6333)

question = "How does dependency injection work?"

# --- Dense results (top 10) ---
question_vector = model.encode(question)
dense_results = client.query_points(
    collection_name="codebase_chunks", query=question_vector.tolist(), limit=10
).points
dense_ranked = [(r.payload["file_path"], r.payload["name"], r.payload["start_line"]) for r in dense_results]

# --- BM25 results (top 10) ---
tokenized_query = tokenize(question)
scores = bm25.get_scores(tokenized_query)
top_bm25_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:10]
bm25_ranked = [(all_chunks[i]["file_path"], all_chunks[i]["name"], all_chunks[i]["start_line"]) for i in top_bm25_indices]

# --- RRF merge ---
k = 60
rrf_scores = {}

for rank, key in enumerate(dense_ranked, start=1):
    rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (k + rank)

for rank, key in enumerate(bm25_ranked, start=1):
    rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (k + rank)

print("Dense top 10:", dense_ranked)
print("BM25 top 10:", bm25_ranked)

final_ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:3]

for (file_path, name, start_line), score in final_ranked:
    print(file_path, "-", name, "- RRF score:", score)