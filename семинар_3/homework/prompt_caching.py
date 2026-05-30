"""
Бенчмарк prompt caching для пайплайна FoodGo.

DeepSeek кэширует одинаковые префиксы входа. Запускаем один и тот же запрос
на аспекты четыре раза и замеряем cache hit/miss и экономию.

Запуск:
    python prompt_caching.py input/reviews.txt
    python prompt_caching.py input/reviews.txt output/cache_report.json
"""

import json
import sys
import time
import uuid
from pathlib import Path

_HOMEWORK = Path(__file__).resolve().parent
_STARTER = _HOMEWORK.parent / "starter"
if str(_HOMEWORK) not in sys.path:
    sys.path.insert(0, str(_HOMEWORK))
if str(_STARTER) not in sys.path:
    sys.path.insert(1, str(_STARTER))

from llm_client import get_model, make_client  # noqa: E402

from pipeline import load_corpus  # noqa: E402
from prompts import ASPECTS_SYSTEM  # noqa: E402
from schema import ReviewSentiment  # noqa: E402

client = make_client()
MODEL = get_model()

# DeepSeek V4 Flash: кэшированные входные токены дешевле (~10×)
PRICE_INPUT_PER_1M = 0.14
PRICE_CACHE_HIT_PER_1M = 0.014


def _usage_dict(completion) -> dict:
    usage = completion.usage
    prompt_tokens = usage.prompt_tokens or 0
    cache_hit = getattr(usage, "prompt_cache_hit_tokens", None) or 0
    cache_miss = getattr(usage, "prompt_cache_miss_tokens", None)
    if cache_miss is None:
        cache_miss = max(prompt_tokens - cache_hit, 0)
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": usage.completion_tokens or 0,
        "cache_hit": cache_hit,
        "cache_miss": cache_miss,
    }


def _cost_usd(info: dict) -> float:
    hit = info["cache_hit"]
    miss = info["cache_miss"]
    out = info["completion_tokens"]
    return (hit / 1_000_000) * PRICE_CACHE_HIT_PER_1M + (
        miss / 1_000_000
    ) * PRICE_INPUT_PER_1M + (out / 1_000_000) * 0.28


def run_once(system_prompt: str, corpus: str) -> dict:
    """Один вызов аспектного анализа: корпус в начале user-сообщения (удобно для кэша)."""
    user_content = (
        f"{corpus}\n\n"
        "---\n"
        "Analyze aspects in ALL reviews above. Return one entry per author."
    )
    t0 = time.time()
    _, completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        response_model=list[ReviewSentiment],
        max_retries=3,
        temperature=0.0,
        with_completion=True,
    )
    info = _usage_dict(completion)
    info["time"] = time.time() - t0
    info["cost_usd"] = _cost_usd(info)
    return info


def run_cache_benchmark(corpus: str) -> dict:
    """Четыре прогона по схеме из раунда 6 семинара."""
    runs: list[dict] = []

    print("━━━ Прогон 1 (холодный) ━━━")
    a = run_once(ASPECTS_SYSTEM, corpus)
    runs.append({"label": "1_cold", "prompt": "original", **a})
    _print_run("первый вызов, оригинальный промпт", a)

    print("\n━━━ Прогон 2 (тот же промпт — ожидаем cache hit) ━━━")
    b = run_once(ASPECTS_SYSTEM, corpus)
    runs.append({"label": "2_repeat", "prompt": "original", **b})
    _print_run("повтор, оригинальный промпт", b)

    print("\n━━━ Прогон 3 (изменён system prompt — кэш должен слететь) ━━━")
    modified = ASPECTS_SYSTEM + f"\n# noise: {uuid.uuid4()}\n"
    c = run_once(modified, corpus)
    runs.append({"label": "3_modified_prompt", "prompt": "modified", **c})
    _print_run("изменённый system prompt", c)

    print("\n━━━ Прогон 4 (восстанавливаем оригинал — кэш вернётся) ━━━")
    d = run_once(ASPECTS_SYSTEM, corpus)
    runs.append({"label": "4_restored", "prompt": "original", **d})
    _print_run("снова оригинальный промпт", d)

    savings = a["cost_usd"] - b["cost_usd"]
    hit_pct_b = b["cache_hit"] / b["prompt_tokens"] * 100 if b["prompt_tokens"] else 0

    report = {
        "model": MODEL,
        "corpus_chars": len(corpus),
        "runs": runs,
        "summary": {
            "run1_cost_usd": round(a["cost_usd"], 6),
            "run2_cost_usd": round(b["cost_usd"], 6),
            "run2_cache_hit_pct": round(hit_pct_b, 1),
            "savings_run2_vs_run1_usd": round(savings, 6),
            "run3_cache_hit_pct": round(
                c["cache_hit"] / c["prompt_tokens"] * 100 if c["prompt_tokens"] else 0, 1
            ),
            "run4_cache_hit_pct": round(
                d["cache_hit"] / d["prompt_tokens"] * 100 if d["prompt_tokens"] else 0, 1
            ),
        },
    }
    return report


def _print_run(label: str, info: dict) -> None:
    total = info["prompt_tokens"]
    hit = info["cache_hit"]
    miss = info["cache_miss"]
    pct = hit / total * 100 if total else 0
    print(
        f"  {label:<34} time={info['time']:>5.1f}s  "
        f"in={total:>6}  hit={hit:>6} ({pct:>4.0f}%)  "
        f"miss={miss:>6}  ${info['cost_usd']:.5f}"
    )


def main() -> None:
    if len(sys.argv) < 2:
        print("Использование: python prompt_caching.py <input/reviews.txt> [output.json]")
        sys.exit(1)
    corpus = load_corpus(sys.argv[1])
    print(f"Модель: {MODEL}, корпус: {len(corpus)} символов\n")
    report = run_cache_benchmark(corpus)

    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output/cache_report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nСохранено: {out_path}")
    s = report["summary"]
    print(
        f"\nЭкономия прогон 2 vs 1: ${s['savings_run2_vs_run1_usd']:.5f} "
        f"(cache hit {s['run2_cache_hit_pct']:.0f}%)"
    )


if __name__ == "__main__":
    main()
