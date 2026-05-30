"""
Пайплайн анализа отзывов FoodGo (вариант A — ДЗ).

Запуск:
    python pipeline.py input/reviews.txt
    python pipeline.py input/reviews.txt output
    python pipeline.py input/reviews.txt output --no-cache
"""

import csv
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

_HOMEWORK = Path(__file__).resolve().parent
_STARTER = _HOMEWORK.parent / "starter"
# Сначала homework — иначе `schema` подхватится из starter/schema.py
if str(_HOMEWORK) not in sys.path:
    sys.path.insert(0, str(_HOMEWORK))
if str(_STARTER) not in sys.path:
    sys.path.insert(1, str(_STARTER))

from llm_client import get_model, make_client  # noqa: E402

from prompts import (  # noqa: E402
    ASPECTS_DISCOVERED_SYSTEM,
    ASPECTS_SYSTEM,
    CHUNK_SYSTEM,
    DISCOVER_SYSTEM,
    IE_SYSTEM,
    JUDGE_SYSTEM,
    REDUCE_SYSTEM,
    REDUCE_SYSTEM_STRICT,
)
from schema import (  # noqa: E402
    ASPECTS,
    AspectSentiment,
    ChunkSummary,
    DiscoveredAspects,
    DynamicReviewSentiment,
    Issue,
    JudgeReport,
    Review,
    ReviewSentiment,
    ReviewsSummary,
    Sentiment,
)

REVIEW_HEADER_RE = re.compile(r"^═+\nОТЗЫВ #\d+\n", re.MULTILINE)

client = make_client()
MODEL = get_model()

PRICE_INPUT_PER_1M = 0.14
PRICE_OUTPUT_PER_1M = 0.28


@dataclass
class UsageTracker:
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0
    validation_errors: int = 0

    def add(self, completion) -> None:
        usage = completion.usage
        self.input_tokens += usage.prompt_tokens or 0
        self.output_tokens += usage.completion_tokens or 0
        self.calls += 1

    def cost_usd(self) -> float:
        return (self.input_tokens / 1_000_000) * PRICE_INPUT_PER_1M + (
            self.output_tokens / 1_000_000
        ) * PRICE_OUTPUT_PER_1M


@dataclass
class PipelineResult:
    reviews: list[Review] = field(default_factory=list)
    aspects: list[ReviewSentiment] = field(default_factory=list)
    aspects_discovered: list[DynamicReviewSentiment] = field(default_factory=list)
    discovered_meta: DiscoveredAspects | None = None
    aspect_comparison: dict = field(default_factory=dict)
    cache_report: dict = field(default_factory=dict)
    summary: ReviewsSummary | None = None
    judge_report: JudgeReport | None = None
    ghost_quotes: list[tuple[str, str]] = field(default_factory=list)
    usage: UsageTracker = field(default_factory=UsageTracker)
    elapsed_sec: float = 0.0


def load_corpus(input_path: str | Path) -> str:
    path = Path(input_path)
    if path.is_dir():
        parts = sorted(path.glob("*.txt"))
        if not parts:
            raise FileNotFoundError(f"No .txt files in {path}")
        return "\n\n".join(p.read_text(encoding="utf-8") for p in parts)
    return path.read_text(encoding="utf-8")


def split_reviews(corpus: str) -> list[str]:
    """Разбить reviews.txt на отдельные блоки отзывов."""
    corpus = corpus.strip()
    if "ОТЗЫВ #" not in corpus:
        return [corpus] if corpus else []

    parts = REVIEW_HEADER_RE.split(corpus)
    chunks: list[str] = []
    headers = REVIEW_HEADER_RE.findall(corpus)
    for header, body in zip(headers, parts[1:]):
        block = header + body.strip()
        if block.strip():
            chunks.append(block)
    return chunks or [corpus]


def _call_with_usage(messages: list[dict], response_model, temperature: float = 0.0):
    result, completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_model=response_model,
        max_retries=3,
        temperature=temperature,
        with_completion=True,
    )
    return result, completion


def extract_review(chunk: str, tracker: UsageTracker) -> Review:
    review, completion = _call_with_usage(
        [
            {"role": "system", "content": IE_SYSTEM},
            {"role": "user", "content": f"Extract one review:\n\n{chunk}"},
        ],
        Review,
        temperature=0.0,
    )
    tracker.add(completion)
    return review


def extract_reviews(chunks: list[str], tracker: UsageTracker, workers: int = 6) -> list[Review]:
    reviews: list[Review | None] = [None] * len(chunks)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(extract_review, c, tracker): i for i, c in enumerate(chunks)}
        for fut in as_completed(futures):
            i = futures[fut]
            try:
                reviews[i] = fut.result()
            except Exception:
                tracker.validation_errors += 1
                raise
    return [r for r in reviews if r is not None]


def extract_aspects_batch(batch: str, tracker: UsageTracker) -> list[ReviewSentiment]:
    result, completion = _call_with_usage(
        [
            {"role": "system", "content": ASPECTS_SYSTEM},
            {"role": "user", "content": f"Analyze aspects in these reviews:\n\n{batch}"},
        ],
        list[ReviewSentiment],
        temperature=0.0,
    )
    tracker.add(completion)
    return result


def extract_aspects(chunks: list[str], tracker: UsageTracker, batch_size: int = 8) -> list[ReviewSentiment]:
    merged: dict[str, ReviewSentiment] = {}
    for i in range(0, len(chunks), batch_size):
        batch = "\n\n".join(chunks[i : i + batch_size])
        for rs in extract_aspects_batch(batch, tracker):
            if rs.author in merged:
                seen = {a.aspect for a in merged[rs.author].aspects}
                for asp in rs.aspects:
                    if asp.aspect not in seen:
                        merged[rs.author].aspects.append(asp)
                        seen.add(asp.aspect)
            else:
                merged[rs.author] = rs
    return list(merged.values())


def discover_aspects(corpus: str, tracker: UsageTracker) -> DiscoveredAspects:
    """Стадия A: модель сама предлагает темы без фиксированного списка."""
    result, completion = _call_with_usage(
        [
            {"role": "system", "content": DISCOVER_SYSTEM},
            {"role": "user", "content": f"Discover themes in these reviews:\n\n{corpus}"},
        ],
        DiscoveredAspects,
        temperature=0.3,
    )
    tracker.add(completion)
    return result


def build_discovered_aspects_system(discovered: DiscoveredAspects) -> str:
    lines = [
        f"  • {a.name} — {a.description}" for a in discovered.aspects
    ]
    return ASPECTS_DISCOVERED_SYSTEM.format(aspect_list="\n".join(lines))


def extract_aspects_discovered_batch(
    batch: str,
    system_prompt: str,
    tracker: UsageTracker,
) -> list[DynamicReviewSentiment]:
    result, completion = _call_with_usage(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze aspects in these reviews:\n\n{batch}"},
        ],
        list[DynamicReviewSentiment],
        temperature=0.0,
    )
    tracker.add(completion)
    return result


def extract_aspects_discovered(
    chunks: list[str],
    discovered: DiscoveredAspects,
    tracker: UsageTracker,
    batch_size: int = 8,
) -> list[DynamicReviewSentiment]:
    """Стадия B: классификация по найденным autodiscovery темам."""
    system_prompt = build_discovered_aspects_system(discovered)
    merged: dict[str, DynamicReviewSentiment] = {}
    for i in range(0, len(chunks), batch_size):
        batch = "\n\n".join(chunks[i : i + batch_size])
        for rs in extract_aspects_discovered_batch(batch, system_prompt, tracker):
            if rs.author in merged:
                seen = {a.aspect for a in merged[rs.author].aspects}
                for asp in rs.aspects:
                    if asp.aspect not in seen:
                        merged[rs.author].aspects.append(asp)
                        seen.add(asp.aspect)
            else:
                merged[rs.author] = rs
    return list(merged.values())


def compare_aspect_approaches(
    fixed: list[ReviewSentiment],
    discovered: list[DynamicReviewSentiment],
    discovered_meta: DiscoveredAspects,
) -> dict:
    fixed_used = {a.aspect for rs in fixed for a in rs.aspects}
    dyn_used = {a.aspect for rs in discovered for a in rs.aspects}
    discovered_names = {a.name for a in discovered_meta.aspects}
    literal_set = set(ASPECTS)

    return {
        "fixed_literal_aspects": sorted(literal_set),
        "fixed_aspects_used_in_labels": sorted(fixed_used),
        "discovered_theme_names": sorted(discovered_names),
        "discovered_aspects_used_in_labels": sorted(dyn_used),
        "new_vs_literal": sorted(dyn_used - literal_set),
        "literal_not_used": sorted(literal_set - fixed_used),
        "discovered_themes_not_used": sorted(discovered_names - dyn_used),
        "fixed_label_count": sum(len(rs.aspects) for rs in fixed),
        "discovered_label_count": sum(len(rs.aspects) for rs in discovered),
    }


def quote_in_text(quote: str, text: str, prefix_len: int = 30) -> bool:
    needle = quote[:prefix_len].lower().strip()
    if not needle:
        return False
    return needle in text.lower()


def check_quotes(
    reviews: list[Review],
    aspects: list[ReviewSentiment],
    corpus: str,
    aspects_discovered: list[DynamicReviewSentiment] | None = None,
) -> list[tuple[str, str]]:
    ghosts: list[tuple[str, str]] = []
    for review in reviews:
        for issue in review.issues:
            if not quote_in_text(issue.quote, corpus):
                ghosts.append((review.author, issue.quote))
    for rs in aspects:
        for asp in rs.aspects:
            if not quote_in_text(asp.quote, corpus):
                ghosts.append((rs.author, asp.quote))
    if aspects_discovered:
        for rs in aspects_discovered:
            for asp in rs.aspects:
                if not quote_in_text(asp.quote, corpus):
                    ghosts.append((rs.author, asp.quote))
    return ghosts


def build_heatmap(
    aspects: list[ReviewSentiment],
    out_path: Path,
    title: str = "FoodGo — фиксированные аспекты",
) -> None:
    authors = sorted({rs.author for rs in aspects})
    aspect_list = list(ASPECTS)
    _render_heatmap(authors, aspect_list, aspects, out_path, title)


def build_heatmap_discovered(
    aspects: list[DynamicReviewSentiment],
    out_path: Path,
    title: str = "FoodGo — autodiscovery аспекты",
) -> None:
    authors = sorted({rs.author for rs in aspects})
    aspect_list = sorted({a.aspect for rs in aspects for a in rs.aspects})
    if not aspect_list:
        return
    _render_heatmap(authors, aspect_list, aspects, out_path, title)


def _render_heatmap(authors, aspect_list, aspects, out_path: Path, title: str) -> None:
    sentiment_map: dict[Sentiment, float] = {
        "positive": 1.0,
        "neutral": 0.0,
        "negative": -1.0,
    }

    matrix = np.full((len(authors), len(aspect_list)), np.nan)
    for i, author in enumerate(authors):
        rs = next((x for x in aspects if x.author == author), None)
        if not rs:
            continue
        for asp in rs.aspects:
            aspect_name = asp.aspect if isinstance(asp.aspect, str) else asp.aspect
            if aspect_name in aspect_list:
                j = aspect_list.index(aspect_name)
                matrix[i, j] = sentiment_map[asp.sentiment]

    plt.figure(figsize=(max(10, len(aspect_list) * 1.2), max(6, len(authors) * 0.35)))
    sns.heatmap(
        matrix,
        xticklabels=aspect_list,
        yticklabels=authors,
        cmap="RdYlGn",
        center=0,
        vmin=-1,
        vmax=1,
        linewidths=0.5,
        cbar_kws={"label": "sentiment"},
    )
    plt.title(title)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()


def summarize_chunk(chunk: str, tracker: UsageTracker) -> ChunkSummary:
    result, completion = _call_with_usage(
        [
            {"role": "system", "content": CHUNK_SYSTEM},
            {"role": "user", "content": chunk},
        ],
        ChunkSummary,
        temperature=0.0,
    )
    tracker.add(completion)
    return result


def reduce_summaries(
    summaries: list[ChunkSummary],
    tracker: UsageTracker,
    *,
    system_prompt: str = REDUCE_SYSTEM,
) -> ReviewsSummary:
    blocks = []
    for s in summaries:
        points = "\n".join(f"  - {p}" for p in s.key_points)
        blocks.append(
            f"Автор: {s.author}, оценка {s.rating}/5, тон {s.sentiment}\n{points}"
        )
    payload = "\n\n---\n\n".join(blocks)
    result, completion = _call_with_usage(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Merge these {len(summaries)} review summaries:\n\n{payload}"},
        ],
        ReviewsSummary,
        temperature=0.2,
    )
    tracker.add(completion)
    return result


def summarize_reviews(
    chunks: list[str],
    tracker: UsageTracker,
    workers: int = 6,
    reduce_prompt: str = REDUCE_SYSTEM,
) -> ReviewsSummary:
    summaries: list[ChunkSummary | None] = [None] * len(chunks)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(summarize_chunk, c, tracker): i for i, c in enumerate(chunks)}
        for fut in as_completed(futures):
            i = futures[fut]
            summaries[i] = fut.result()
    return reduce_summaries([s for s in summaries if s is not None], tracker, system_prompt=reduce_prompt)


def build_evidence_packet(reviews: list[Review], summary: ReviewsSummary) -> str:
    lines = ["## Action items to evaluate\n"]
    for i, action in enumerate(summary.action_items, 1):
        lines.append(f"{i}. {action}")

    lines.append("\n## Extracted review issues (ground truth)\n")
    for review in reviews:
        lines.append(f"### {review.author} ({review.rating}/5, {review.store})")
        if not review.issues:
            lines.append("  (no issues extracted)")
        for issue in review.issues:
            lines.append(
                f"  - [{issue.category}] {issue.description}\n"
                f"    quote: «{issue.quote}»"
            )
    return "\n".join(lines)


def judge(reviews: list[Review], summary: ReviewsSummary, tracker: UsageTracker) -> JudgeReport:
    packet = build_evidence_packet(reviews, summary)
    result, completion = _call_with_usage(
        [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": packet},
        ],
        JudgeReport,
        temperature=0.0,
    )
    tracker.add(completion)
    return result


def save_reviews_csv(reviews: list[Review], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "author",
                "rating",
                "store",
                "review_date",
                "title",
                "n_issues",
                "issue_categories",
            ],
        )
        writer.writeheader()
        for r in reviews:
            writer.writerow(
                {
                    "author": r.author,
                    "rating": r.rating,
                    "store": r.store,
                    "review_date": r.review_date.isoformat(),
                    "title": r.title or "",
                    "n_issues": len(r.issues),
                    "issue_categories": ";".join(i.category for i in r.issues),
                }
            )


def analyze(input_path: str, out_dir: str = "output", *, run_cache_benchmark: bool = True) -> PipelineResult:
    """Полный конвейер: отзывы → IE → аспекты → autodiscovery → MR → judge → cache."""
    t0 = time.time()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    tracker = UsageTracker()
    corpus = load_corpus(input_path)
    chunks = split_reviews(corpus)
    print(f"Загружено: {len(chunks)} отзывов, {len(corpus)} символов")

    print("\n[1/6] IE — извлечение отзывов...")
    reviews = extract_reviews(chunks, tracker)
    reviews_path = out / "reviews.json"
    reviews_path.write_text(
        json.dumps([r.model_dump(mode="json") for r in reviews], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    save_reviews_csv(reviews, out / "reviews.csv")
    print(f"  ✓ {len(reviews)} отзывов → {reviews_path.name}")

    print("\n[2/6] Аспектный анализ (fixed Literal)...")
    aspects = extract_aspects(chunks, tracker)
    aspects_path = out / "aspects.json"
    aspects_path.write_text(
        json.dumps([a.model_dump(mode="json") for a in aspects], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    build_heatmap(aspects, out / "heatmap.png")
    print(f"  ✓ {len(aspects)} авторов → {aspects_path.name}")

    print("\n[3/6] Autodiscovery — stage A + B...")
    discovered_meta = discover_aspects(corpus, tracker)
    (out / "discovered_themes.json").write_text(
        discovered_meta.model_dump_json(indent=2),
        encoding="utf-8",
    )
    print(f"  ✓ Stage A: {len(discovered_meta.aspects)} тем")
    for theme in discovered_meta.aspects[:5]:
        print(f"      • {theme.name}")
    if len(discovered_meta.aspects) > 5:
        print(f"      … и ещё {len(discovered_meta.aspects) - 5}")

    aspects_discovered = extract_aspects_discovered(chunks, discovered_meta, tracker)
    (out / "aspects_discovered.json").write_text(
        json.dumps(
            [a.model_dump(mode="json") for a in aspects_discovered],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    build_heatmap_discovered(aspects_discovered, out / "heatmap_discovered.png")
    aspect_comparison = compare_aspect_approaches(aspects, aspects_discovered, discovered_meta)
    (out / "aspect_discovery_report.json").write_text(
        json.dumps(aspect_comparison, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if aspect_comparison["new_vs_literal"]:
        print(f"  ✓ Stage B: новые темы vs Literal: {aspect_comparison['new_vs_literal'][:3]}")
    else:
        print("  ✓ Stage B: классификация по найденным темам")

    ghosts = check_quotes(reviews, aspects, corpus, aspects_discovered)
    ghost_pct = len(ghosts) / max(
        sum(len(r.issues) for r in reviews)
        + sum(len(a.aspects) for a in aspects)
        + sum(len(a.aspects) for a in aspects_discovered),
        1,
    ) * 100
    print(f"  ghost-цитат: {len(ghosts)} ({ghost_pct:.1f}%)")

    print("\n[4/6] Map-Reduce — сводка...")
    chunk_summaries: list[ChunkSummary | None] = [None] * len(chunks)
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(summarize_chunk, c, tracker): i for i, c in enumerate(chunks)}
        for fut in as_completed(futures):
            i = futures[fut]
            chunk_summaries[i] = fut.result()
    mapped = [s for s in chunk_summaries if s is not None]
    summary = reduce_summaries(mapped, tracker)
    summary_path = out / "summary.json"
    summary_path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    print(f"  ✓ {summary.headline[:80]}...")

    print("\n[5/6] LLM-as-judge...")
    report = judge(reviews, summary, tracker)
    if report.overall_score < 0.7:
        print(f"  ⚠ score {report.overall_score:.2f} < 0.7 — повтор REDUCE (strict)...")
        summary = reduce_summaries(mapped, tracker, system_prompt=REDUCE_SYSTEM_STRICT)
        report = judge(reviews, summary, tracker)
        summary_path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    judge_path = out / "judge_report.json"
    judge_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    print(f"  ✓ overall_score={report.overall_score:.2f}")

    cache_report: dict = {}
    if run_cache_benchmark:
        print("\n[6/6] Prompt caching benchmark...")
        from prompt_caching import run_cache_benchmark as _run_cache

        cache_report = _run_cache_benchmark(corpus)
        (out / "cache_report.json").write_text(
            json.dumps(cache_report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        s = cache_report["summary"]
        print(
            f"  ✓ cache hit run2: {s['run2_cache_hit_pct']:.0f}%, "
            f"savings ${s['savings_run2_vs_run1_usd']:.5f}"
        )

    elapsed = time.time() - t0
    metrics = {
        "input_reviews": len(chunks),
        "extracted_reviews": len(reviews),
        "validation_errors": tracker.validation_errors,
        "ghost_quotes": len(ghosts),
        "ghost_quote_pct": round(ghost_pct, 2),
        "ghost_quote_samples": [{"author": a, "quote": q[:120]} for a, q in ghosts[:5]],
        "overall_score": report.overall_score,
        "aspect_discovery": aspect_comparison,
        "cache_summary": cache_report.get("summary"),
        "elapsed_sec": round(elapsed, 1),
        "llm_calls": tracker.calls,
        "input_tokens": tracker.input_tokens,
        "output_tokens": tracker.output_tokens,
        "cost_usd": round(tracker.cost_usd(), 4),
    }
    (out / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result = PipelineResult(
        reviews=reviews,
        aspects=aspects,
        aspects_discovered=aspects_discovered,
        discovered_meta=discovered_meta,
        aspect_comparison=aspect_comparison,
        cache_report=cache_report,
        summary=summary,
        judge_report=report,
        ghost_quotes=ghosts,
        usage=tracker,
        elapsed_sec=elapsed,
    )

    print("\n━━━ ИТОГ ━━━")
    print(f"  Отзывов:       {len(reviews)}")
    print(f"  Ghost-цитат:   {len(ghosts)}")
    print(f"  Judge score:   {report.overall_score:.2f}")
    print(f"  Autodiscovery: {len(discovered_meta.aspects)} тем, "
          f"{len(aspect_comparison.get('new_vs_literal', []))} новых vs Literal")
    if cache_report:
        print(f"  Cache savings: ${cache_report['summary']['savings_run2_vs_run1_usd']:.5f}")
    print(f"  Время:         {elapsed:.1f} с")
    print(f"  Стоимость:     ${tracker.cost_usd():.4f}")
    print(f"  Артефакты:     {out.resolve()}/")
    return result


def main() -> None:
    if len(sys.argv) < 2:
        print("Использование: python pipeline.py <input/reviews.txt> [output_dir] [--no-cache]")
        sys.exit(1)
    input_path = sys.argv[1]
    args = sys.argv[2:]
    output_dir = "output"
    run_cache = True
    for arg in args:
        if arg == "--no-cache":
            run_cache = False
        elif not arg.startswith("-"):
            output_dir = arg
    analyze(input_path, output_dir, run_cache_benchmark=run_cache)


if __name__ == "__main__":
    main()
