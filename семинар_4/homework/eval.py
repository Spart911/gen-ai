from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline import STRATEGIES, get_collection, hybrid_retrieve, retrieve

GOLD_PATH = Path(__file__).parent / "data" / "gold.json"
RESULTS_PATH = Path(__file__).parent / "eval_results.json"
COMPARISON_PATH = Path(__file__).parent / "chunking_comparison.json"


def load_gold() -> list[dict]:
    return json.loads(GOLD_PATH.read_text(encoding="utf-8"))


def hit_rate(retrieved_ids: list[str], gold_sources: list[str]) -> float:
    retrieved_sources = {rid.split("__")[0] for rid in retrieved_ids}
    found = [g for g in gold_sources if g in retrieved_sources]
    return len(found) / len(gold_sources)


def gold_ranks(retrieved_ids: list[str], gold_sources: list[str]) -> list[int | None]:
    sources = [rid.split("__")[0] for rid in retrieved_ids]
    ranks: list[int | None] = []
    for g in gold_sources:
        ranks.append(sources.index(g) + 1 if g in sources else None)
    return ranks


def run_eval(
    strategy: str,
    *,
    dense_only: bool = False,
    k: int = 5,
    verbose: bool = True,
) -> dict:
    gold = load_gold()
    col = get_collection(strategy)
    if col.count() == 0:
        raise SystemExit(
            f"Коллекция [{strategy}] пустая. "
            f"Запустите: python pipeline.py ingest --strategy {strategy}"
        )

    fn = (lambda q, k=k: retrieve(q, k=k, strategy=strategy)) if dense_only else (
        lambda q, k=k: hybrid_retrieve(q, k=k, strategy=strategy)
    )
    label = "DENSE-ONLY" if dense_only else "HYBRID (DENSE + BM25 + RRF)"
    if verbose:
        print(f"\n=== {label} | strategy={strategy} ===\n")

    total = 0.0
    rank_sum = 0
    rank_count = 0
    results = []
    for item in gold:
        hits = fn(item["question"], k=k)
        retrieved_ids = hits["ids"][0]
        score = hit_rate(retrieved_ids, item["gold_sources"])
        ranks = gold_ranks(retrieved_ids, item["gold_sources"])
        for r in ranks:
            if r is not None:
                rank_sum += r
                rank_count += 1
        total += score
        row = {
            "id": item["id"],
            "type": item["type"],
            "question": item["question"],
            "score": score,
            "gold": item["gold_sources"],
            "retrieved_ids": retrieved_ids,
            "retrieved_sources": [rid.split("__")[0] for rid in retrieved_ids],
            "gold_ranks": ranks,
        }
        results.append(row)
        if verbose:
            mark = "✓" if score == 1.0 else ("◐" if score > 0 else "✗")
            print(f"  [{item['id']:2d}] {item['type']:25s}  hit@{k} = {score:.2f}  {mark}")

    mean = total / len(gold)
    avg_rank = rank_sum / rank_count if rank_count else 0.0
    summary = {
        "strategy": strategy,
        "dense_only": dense_only,
        "k": k,
        "mean": mean,
        "total_hits": total,
        "questions": len(gold),
        "chunk_count": col.count(),
        "avg_gold_rank": round(avg_rank, 2),
        "results": results,
    }
    if verbose:
        print(f"\n  ИТОГО: hit-rate@{k} = {mean:.2f}  ({total:.1f} / {len(gold)})")
        print(f"  Чанков в индексе: {col.count()}, средний ранг gold-дока: {avg_rank:.2f}")
    return summary


def build_comparison(*, k: int = 5) -> dict:
    hybrid = {s: run_eval(s, dense_only=False, k=k, verbose=False) for s in STRATEGIES}
    dense = {s: run_eval(s, dense_only=True, k=k, verbose=False) for s in STRATEGIES}

    per_question = []
    for i, item in enumerate(load_gold()):
        row = {
            "id": item["id"],
            "type": item["type"],
            "gold_sources": item["gold_sources"],
            "fixed_hybrid": hybrid["fixed"]["results"][i]["score"],
            "recursive_hybrid": hybrid["recursive"]["results"][i]["score"],
            "fixed_dense": dense["fixed"]["results"][i]["score"],
            "recursive_dense": dense["recursive"]["results"][i]["score"],
        }
        row["hybrid_diff"] = row["fixed_hybrid"] - row["recursive_hybrid"]
        per_question.append(row)

    return {
        "k": k,
        "retrieval": "hybrid = ChromaDB dense + BM25 + RRF",
        "strategies": {
            "fixed": {
                "description": "text[i:i+2000], без overlap",
                "chunk_count": hybrid["fixed"]["chunk_count"],
                "hit_rate_hybrid": hybrid["fixed"]["mean"],
                "hit_rate_dense_only": dense["fixed"]["mean"],
                "avg_gold_rank_hybrid": hybrid["fixed"]["avg_gold_rank"],
            },
            "recursive": {
                "description": "RecursiveCharacterTextSplitter(400, overlap=80)",
                "chunk_count": hybrid["recursive"]["chunk_count"],
                "hit_rate_hybrid": hybrid["recursive"]["mean"],
                "hit_rate_dense_only": dense["recursive"]["mean"],
                "avg_gold_rank_hybrid": hybrid["recursive"]["avg_gold_rank"],
            },
        },
        "per_question": per_question,
        "hybrid": hybrid,
        "dense_only": dense,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", choices=STRATEGIES, default="recursive")
    parser.add_argument("--compare", action="store_true", help="Сравнить fixed vs recursive")
    parser.add_argument("--dense-only", action="store_true")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if args.compare:
        for strategy in STRATEGIES:
            run_eval(
                strategy,
                dense_only=False,
                k=args.k,
                verbose=not args.quiet,
            )
        comparison = build_comparison(k=args.k)
        if not args.quiet:
            print("\n=== СРАВНЕНИЕ ЧАНКИНГА (hybrid, hit-rate@5) ===")
            for name, cfg in comparison["strategies"].items():
                print(
                    f"  {name:10s}  hit@{args.k}={cfg['hit_rate_hybrid']:.2f}  "
                    f"chunks={cfg['chunk_count']}  avg_rank={cfg['avg_gold_rank_hybrid']:.2f}"
                )
            print("\n=== dense-only baseline ===")
            for name, cfg in comparison["strategies"].items():
                print(f"  {name:10s}  hit@{args.k}={cfg['hit_rate_dense_only']:.2f}")

        RESULTS_PATH.write_text(
            json.dumps(comparison["hybrid"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        COMPARISON_PATH.write_text(
            json.dumps(
                {k: v for k, v in comparison.items() if k not in ("hybrid", "dense_only")},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\nСохранено: {RESULTS_PATH.name}, {COMPARISON_PATH.name}")
        return

    run_eval(
        args.strategy,
        dense_only=args.dense_only,
        k=args.k,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
