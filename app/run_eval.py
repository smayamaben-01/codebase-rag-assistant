from rag_pipeline import retrieve
from eval_set import eval_set

def normalize_path(path):
    # Windows paths use backslashes; normalize for comparison
    return path.replace("\\", "/").replace("../data/fastapi-src/", "")

results_summary = []

for item in eval_set:
    question = item["question"]
    expected_files = set(item["expected_files"])

    retrieved_chunks = retrieve(question, top_k=5)
    retrieved_files = [normalize_path(c["file_path"]) for c in retrieved_chunks]

    # Precision: how many retrieved chunks came from an expected file
    relevant_retrieved = sum(1 for f in retrieved_files if f in expected_files)
    precision = relevant_retrieved / len(retrieved_files) if retrieved_files else 0

    # Recall: how many expected files were found (at least once) in retrieved results
    found_expected = expected_files.intersection(set(retrieved_files))
    recall = len(found_expected) / len(expected_files) if expected_files else 0

    results_summary.append({
        "question": question,
        "precision": precision,
        "recall": recall,
        "retrieved_files": retrieved_files
    })

    print(f"Q: {question}")
    print(f"  Precision@5: {precision:.2f} | Recall: {recall:.2f}")
    print(f"  Retrieved: {retrieved_files}")
    print()

avg_precision = sum(r["precision"] for r in results_summary) / len(results_summary)
avg_recall = sum(r["recall"] for r in results_summary) / len(results_summary)
print(f"=== AVERAGE Precision@5: {avg_precision:.2f} | AVERAGE Recall: {avg_recall:.2f} ===")