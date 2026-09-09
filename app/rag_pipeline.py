from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import ollama

model = SentenceTransformer('all-MiniLM-L6-v2')
client = QdrantClient(host="localhost", port=6333)

question = "How does dependency injection work?"
question_vector = model.encode(question)

results = client.query_points(
    collection_name="codebase_chunks",
    query=question_vector.tolist(),
    limit=3
).points

context = ""

for r in results:
    context += f"\n\n--- File: {r.payload['file_path']} ---\n{r.payload['text']}"

prompt = f"""Answer the question using ONLY the code context below. Cite the file path(s) you used.

Context:
{context}

Question: {question}

Answer:"""

response = ollama.chat(model='llama3.1:8b', messages=[
    {'role': 'user', 'content': prompt}
])

print(response['message']['content'])