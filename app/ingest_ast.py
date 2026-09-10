import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from ast_chunker import extract_chunks

folder = "../data/fastapi-src/fastapi"
model = SentenceTransformer('all-MiniLM-L6-v2')
client = QdrantClient(host="localhost", port=6333)

points = []

client.delete_collection("codebase_chunks")
client.create_collection(
    collection_name="codebase_chunks",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

for root, dirs, files in os.walk(folder):
    for filename in files:
        if filename.endswith(".py"):
            full_path = os.path.join(root, filename)
            chunks = extract_chunks(full_path)

            for chunk in chunks:
                embed_text = chunk["docstring"] + "\n" + chunk["code"]
                vector = model.encode(embed_text)

                points.append(
                    PointStruct(
                        id=len(points),
                        vector=vector.tolist(),
                        payload=chunk
                    )
                )
            print(f"Processed: {full_path} ({len(chunks)} chunks)")

client.upsert(collection_name="codebase_chunks", points=points)
print(f"Upload done! {len(points)} points uploaded.")