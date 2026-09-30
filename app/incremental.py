import subprocess
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, PointStruct
from sentence_transformers import SentenceTransformer
from ast_chunker import extract_chunks
import os

def get_changed_files(old_commit, new_commit):
    result = subprocess.run(
        ["git", "diff", "--name-only", old_commit, new_commit],
        capture_output=True,
        text=True,
        cwd="../data/fastapi-src"
    )
    files = result.stdout.strip().split("\n")
    return [f for f in files if f.endswith(".py") and f.startswith("fastapi/")]

client = QdrantClient(host="localhost", port=6333)
model = SentenceTransformer('all-MiniLM-L6-v2')

def reindex_file(full_path_in_repo):
    # full_path_in_repo looks like "fastapi/routing.py" — matches what's stored in payloads
    normalized = full_path_in_repo  # already in the right format from git diff

    # Step 1: delete old chunks for this file
    client.delete(
        collection_name="codebase_chunks",
        points_selector=Filter(
            must=[FieldCondition(key="file_path", match=MatchValue(value=normalized))]
        )
    )
    print(f"Deleted old chunks for: {normalized}")

    # Step 2: re-chunk and re-embed the current version of the file
    real_path = os.path.join("../data/fastapi-src", normalized)
    if not os.path.exists(real_path):
        print(f"File no longer exists (was deleted): {normalized}")
        return

    new_chunks = extract_chunks(real_path)
    points = []
    for c in new_chunks:
        embed_text = c["docstring"] + "\n" + c["code"]
        vector = model.encode(embed_text)
        points.append(PointStruct(
            id=hash((normalized, c["name"], c["start_line"])) & 0x7FFFFFFF,
            vector=vector.tolist(),
            payload={**c, "file_path": normalized}
        ))

    if points:
        client.upsert(collection_name="codebase_chunks", points=points)
    print(f"Re-indexed {len(points)} chunks for: {normalized}")

LAST_COMMIT_FILE = "last_indexed_commit.txt"

def get_last_indexed_commit():
    if os.path.exists(LAST_COMMIT_FILE):
        with open(LAST_COMMIT_FILE, "r") as f:
            return f.read().strip()
    return None  # first run ever, no previous commit

def save_last_indexed_commit(commit_hash):
    with open(LAST_COMMIT_FILE, "w") as f:
        f.write(commit_hash)

def get_current_commit():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True, cwd="../data/fastapi-src"
    )
    return result.stdout.strip()

if __name__ == "__main__":
    last_commit = get_last_indexed_commit()
    current_commit = get_current_commit()

    print(f"last_commit = '{last_commit}'")
    print(f"current_commit = '{current_commit}'")

    if last_commit is None:
        print("No previous index found — run full ingestion first.")
    elif last_commit == current_commit:
        print("No changes since last index.")
    else:
        changed = get_changed_files(last_commit, current_commit)
        print(f"Changed files: {changed}")
        for f in changed:
            reindex_file(f)
        save_last_indexed_commit(current_commit)
        print(f"Index updated to commit: {current_commit}")