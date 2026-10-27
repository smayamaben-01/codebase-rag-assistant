"""Per-question breakdown of the retrieval eval.

Run from the project root, with Qdrant up:
    python -m app.eval_diagnostic
"""
from .rag_pipeline import retrieve, normalize_path
from .eval_set import eval_set

MODES = ["dense", "bm25", "hybrid", "rerank"]
TOP_K = 5


def files_for(question, mode):
    chunks = retrieve(question, top_k=TOP_K, mode=mode)
    return [normalize_path(c["file_path"]) for c in chunks]


def first_rank(files, expected):
    for rank, f in enumerate(files, start=1):
        if f in expected:
            return rank
    return None


def rank_value(rank):
    # a miss counts as worse than any real rank
    return rank if rank is not None else 99


def show(rank):
    return str(rank) if rank is not None else "-"


if __name__ == "__main__":
    rows = []
    for i, item in enumerate(eval_set, start=1):
        expected = set(item["expected_files"])
        retrieved = {m: files_for(item["question"], m) for m in MODES}
        ranks = {m: first_rank(retrieved[m], expected) for m in MODES}
        rows.append((i, item, expected, retrieved, ranks))

    print("Rank of the first correct file in the top 5 ('-' = not found)")
    print(f"{'#':>2}  {'question':<46}" + "".join(f"{m:>8}" for m in MODES))
    for i, item, expected, retrieved, ranks in rows:
        cells = "".join(f"{show(ranks[m]):>8}" for m in MODES)
        print(f"{i:>2}  {item['question'][:44]:<46}{cells}")

    better = worse = same = 0
    worse_rows = []
    for i, item, expected, retrieved, ranks in rows:
        h = rank_value(ranks["hybrid"])
        r = rank_value(ranks["rerank"])
        if r < h:
            better += 1
        elif r > h:
            worse += 1
            worse_rows.append((i, item, ranks))
        else:
            same += 1
    print(f"\nRe-ranking vs hybrid: better on {better}, worse on {worse}, same on {same} questions")

    if worse_rows:
        print("\nQuestions where re-ranking placed the right file lower than hybrid:")
        for i, item, ranks in worse_rows:
            print(f"  #{i} hybrid={show(ranks['hybrid'])} rerank={show(ranks['rerank'])}: {item['question']}")

    print("\nQuestions every mode missed (is the expected file right?):")
    for i, item, expected, retrieved, ranks in rows:
        if all(ranks[m] is None for m in MODES):
            print(f"  #{i} {item['question']}")
            print(f"      expected  : {sorted(expected)}")
            print(f"      rerank got: {retrieved['rerank']}")