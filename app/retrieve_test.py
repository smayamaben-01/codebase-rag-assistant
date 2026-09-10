from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

model = SentenceTransformer('all-MiniLM-L6-v2')
client = QdrantClient(host="localhost", port=6333)

question = "How does dependency injection work?"
question_vector = model.encode(question)

results = client.query_points(
    collection_name="codebase_chunks",
    query=question_vector.tolist(),
    limit=3
).points

for r in results:
    print(r.payload["file_path"], "-", r.payload["name"], "- score:", r.score)