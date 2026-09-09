import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

folder = "../data/fastapi-src/fastapi"
model = SentenceTransformer('all-MiniLM-L6-v2')
client = QdrantClient(host="localhost", port=6333)

points = []

for i, (root, dirs, files) in enumerate(os.walk(folder)):
    for filename in files:
        if filename.endswith(".py"):
            full_path = os.path.join(root, filename)

            with open(full_path, "r", encoding="utf-8") as f:
                chunk_text = f.read()

            vector = model.encode(chunk_text)

            points.append(
                PointStruct(
                    id=len(points),
                    vector=vector.tolist(),
                    payload={"file_path": full_path, "text": chunk_text}
                )
            )
            print(f"Processed: {full_path}")

client.upsert(collection_name="codebase_chunks", points=points)
print(f"Upload done! {len(points)} points uploaded.")