import time
from .rag_pipeline import retrieve, normalize_path
from .eval_set import eval_set

MODES = ["dense", "bm25", "hybrid", "rerank"]
TOP_K = 5


def score(item, mode):
    expected = set(item["expected_files"])
    chunks = retrieve(item["question"], top_k=TOP_K, mode=mode)
    files = [normalize_path(c["file_path"]) for c in chunks]

    precision = sum(f in expected for f in files) / len(files) if files else 0.0
    recall = len(expected & set(files)) / len(expected)

    reciprocal_rank = 0.0
    for rank, f in enumerate(files, start=1):
        if f in expected:
            reciprocal_rank = 1 / rank
            break
    return precision, recall, reciprocal_rank


def average(rows, idx):
    return sum(r[idx] for r in rows) / len(rows)


if __name__ == "__main__":
    results = {m: [] for m in MODES}  # rows of (precision, recall, mrr, is_edge_case)

    for mode in MODES:
        t0 = time.time()
        for item in eval_set:
            p, r, rr = score(item, mode)
            results[mode].append((p, r, rr, "note" in item))
        print(f"finished {mode} in {time.time() - t0:.0f}s", flush=True)
    print()

    def table(title, include):
        print(title)
        print(f"{'mode':<8}{'P@5':>8}{'Recall':>8}{'MRR':>8}")
        for mode in MODES:
            rows = [r for r in results[mode] if include(r)]
            print(f"{mode:<8}{average(rows, 0):>8.2f}{average(rows, 1):>8.2f}{average(rows, 2):>8.2f}")
        print()

    table(f"All {len(eval_set)} questions", lambda r: True)
    table("Excluding the known edge case (CORS re-export)", lambda r: not r[3])