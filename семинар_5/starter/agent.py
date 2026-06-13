"""
Макро-агент: ReAct + вызов инструментов:
  блоки 1-3 — базовый агент: исполняем инструменты, отвечает текстом.
  блок 5    — новый инструмент get_unemployment + тяжёлые multi-hop задачи.
  блок 6    — параллельные вызовы инструментов (флаг --parallel).
  блок 7    — структурированный ответ через submit_answer (флаг --structured).
  блок 8    — самопроверка перед ответом (флаг --critic).
  блок 9    — кэш детерминированных инструментов (флаг --cache).
  блок 10   — учёт токенов и стоимости (флаг --cost).

Запуск:
    python agent.py "Какая реальная ключевая ставка сейчас?"
    python agent.py --parallel --structured --critic "Сравни курс USD сегодня и 2 января 2022"
    python agent.py --cost "Что сейчас выше: ключевая ставка или индекс нищеты?"

"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_client import get_model, make_client, make_raw_client
from schemas import TOOL_SCHEMAS
from tools import (
    calculate,
    compare_periods,
    get_fx_rate,
    get_inflation,
    get_key_rate,
    get_unemployment,
)

# набор инструментов
TOOLS_IMPL = {
    "get_fx_rate": get_fx_rate,
    "get_key_rate": get_key_rate,
    "get_inflation": get_inflation,
    "get_unemployment": get_unemployment,
    "compare_periods": compare_periods,
    "calculate": calculate,
}

TRACE_PATH = Path(__file__).resolve().parent / "trace.jsonl"


# блок 7 — структурированный ответ
class AgentAnswer(BaseModel):
    answer: str = Field(description="Human-readable answer, one or two sentences")
    value: Optional[float] = Field(default=None, description="Main numeric answer")
    unit: Optional[str] = Field(default=None, description="Unit: %, rub, year")
    sources: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


SUBMIT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "submit_answer",
        "description": "Call ONLY when there is enough data for the final answer. "
        "Submit the answer as a structured object, not as plain text.",
        "parameters": {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "value": {"type": ["number", "null"]},
                "unit": {"type": ["string", "null"]},
                "sources": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number"},
            },
            "required": ["answer", "confidence"],
        },
    },
}


# блок 8 — самопроверка
class CriticVerdict(BaseModel):
    ok: bool
    issue: str = ""


CRITIC_SYSTEM = """You are a meticulous reviewer. You receive the agent's final answer and
the tool log. Check ONE thing: does the number in the answer follow from the tool
data, without fabrication? ok=false if the number is not confirmed by the log or
the arithmetic does not add up. issue — one sentence explaining what is wrong."""


# блок 9 — кэш детерминированных инструментов (живёт в пределах процесса).
TOOL_CACHE: dict[str, dict] = {}
CACHE_STATS = {"hits": 0, "misses": 0}

# блок 10 — грубая оценка стоимости. Цена за 1 млн токенов, USD (ориентир DeepSeek).
PRICE_IN_PER_MTOK = 0.14
PRICE_OUT_PER_MTOK = 0.28


_BASE_RULES = """\
You are a macroeconomic analyst with Bank of Russia and Rosstat data. NEVER
INVENT NUMBERS — obtain them via tools.

Tools:
- get_fx_rate: currency-to-ruble exchange rate on a date
- get_key_rate: Bank of Russia key rate on a date
- get_inflation: CPI (% y/y) at month-end
- get_unemployment: unemployment (% of labor force) at month-end
- compare_periods: compare one metric across two periods (delta, ratio)
- calculate: safe calculator for arithmetic on obtained numbers

Algorithm:
1. Break down the question: which numbers are needed and in what order. If
   several numbers are independent — request them in one step (multiple calls at once).
2. Do arithmetic ONLY via calculate.
3. Real rate = nominal rate − y/y inflation.
4. Real deposit return ≈ (1 + rate/100) / (1 + inflation/100) − 1.
5. Misery index = y/y inflation + unemployment.
6. Cross-rate "how many B per 1 A" = (rubles per 1 A) / (rubles per 1 B).
   Example: "yuan per dollar" = (rubles per dollar) / (rubles per yuan).
"""

SYSTEM_PROMPT = (
    _BASE_RULES
    + """\
7. When there is enough data — give the final answer as plain text WITHOUT tool
   calls. One or two sentences, with numbers and units. If a number comes from
   fallback_csv — note that the Bank of Russia is momentarily unavailable.
Date format — YYYY-MM-DD.
Current date: {}
""".format(datetime.datetime.now().strftime("%Y-%m-%d"))
)

SYSTEM_PROMPT_PRO = (
    _BASE_RULES
    + """\
7. When there is enough data — do NOT write text; call submit_answer with
   structure (answer, value, unit, sources, confidence).
Date format — YYYY-MM-DD.
"""
)


def _trace_ts() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _append_trace_line(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _log_trace_event(
    path: Optional[Path],
    run_id: str,
    event: dict,
) -> None:
    if path is None:
        return
    _append_trace_line(path, {"run_id": run_id, "ts": _trace_ts(), **event})


def _exec_one(tc, cache: Optional[dict] = None) -> tuple[Any, dict, dict]:
    """Исполнить один вызов инструмента. Вернуть (tc, args, obs).
    Любую ошибку превращаем в obs={'error': ...}, чтобы агент мог переиграть."""
    name = tc.function.name
    try:
        args = json.loads(tc.function.arguments or "{}")
    except JSONDecodeError as e:
        return tc, {}, {"error": f"malformed tool arguments JSON: {e}"}

    fn = TOOLS_IMPL.get(name)
    if fn is None:
        return tc, args, {"error": f"unknown tool: {name}"}

    key = name + ":" + json.dumps(args, sort_keys=True, ensure_ascii=False)
    if cache is not None and key in cache:
        CACHE_STATS["hits"] += 1
        return tc, args, cache[key]

    try:
        obs = fn(**args)
    except TypeError as e:
        return (
            tc,
            args,
            {
                "error": f"bad arguments for {name}: {e}. Expected: {fn.__annotations__}"
            },
        )
    except Exception as e:
        return tc, args, {"error": f"{type(e).__name__}: {e}"}

    if cache is not None and "error" not in obs:
        CACHE_STATS["misses"] += 1
        cache[key] = obs
    return tc, args, obs


def critique(answer: AgentAnswer, tool_log: list[dict]) -> CriticVerdict:
    ic = make_client()
    facts = "\n".join(
        f"{e['call']}({e['args']}) -> {json.dumps(e['obs'], ensure_ascii=False)}"
        for e in tool_log
        if "call" in e
    )
    return ic.chat.completions.create(
        model=get_model(),
        response_model=CriticVerdict,
        max_retries=2,
        temperature=0.0,
        messages=[
            {"role": "system", "content": CRITIC_SYSTEM},
            {
                "role": "user",
                "content": f"Agent answer: «{answer.answer}» (value={answer.value} {answer.unit}).\n"
                f"Tool log:\n{facts or '(empty)'}",
            },
        ],
    )


def _finish(
    res: dict,
    usage_log: list[dict],
    *,
    track_cost: bool,
    use_cache: bool,
    verbose: bool,
) -> dict:
    """Прикрепить к результату учёт токенов/стоимости (блок 10) и статистику
    кэша (блок 9); по флагам — распечатать. Этот код готов; чтобы таблица
    стоимости заполнилась, надо заполнить usage_log в run_agent (блок 10)."""
    total_in = sum(u["prompt_tokens"] for u in usage_log)
    total_out = sum(u["completion_tokens"] for u in usage_log)
    total_cost = round(sum(u["cost_usd"] for u in usage_log), 6)
    res["usage"] = {
        "prompt_tokens": total_in,
        "completion_tokens": total_out,
        "cost_usd": total_cost,
        "by_step": usage_log,
    }
    if use_cache:
        res["cache"] = dict(CACHE_STATS)

    if track_cost and usage_log:
        print("\n  шаг | вход.ток | выход.ток |   $/шаг |  $ накоп.")
        acc = 0.0
        for u in usage_log:
            acc += u["cost_usd"]
            print(
                f"  {u['step']:>3} | {u['prompt_tokens']:>8} | {u['completion_tokens']:>9} | "
                f"{u['cost_usd']:.5f} | {acc:.5f}"
            )
        print(
            f"  Итого: {total_in} вход + {total_out} выход токенов, ~${total_cost:.5f}."
        )
    if use_cache and verbose:
        print(
            f"  [кэш] попаданий {CACHE_STATS['hits']}, промахов {CACHE_STATS['misses']}"
        )
    return res


def run_agent(
    user_query: str,
    *,
    max_iter: int = 8,
    parallel: bool = False,
    structured: bool = False,
    use_critic: bool = False,
    use_cache: bool = False,
    track_cost: bool = False,
    verbose: bool = True,
    trace_path: Optional[Path] = None,
    run_id: Optional[str] = None,
) -> dict[str, Any]:
    """ReAct-цикл. базовый режим — финал текстом; флаги включают блоки 6-10."""
    client = make_raw_client()
    model = get_model()
    tools = TOOL_SCHEMAS + ([SUBMIT_SCHEMA] if structured else [])
    system = SYSTEM_PROMPT_PRO if structured else SYSTEM_PROMPT
    cache = TOOL_CACHE if use_cache else None
    run_id = run_id or str(uuid.uuid4())
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_query},
    ]
    trace: list[dict[str, Any]] = []
    usage_log: list[dict[str, Any]] = []  # блок 10 — токены по шагам

    for step in range(1, max_iter + 1):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.0,
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        # блок 10 — учёт токенов шага
        u = getattr(resp, "usage", None)
        if u is not None:
            pin, pout = u.prompt_tokens, u.completion_tokens
            cost = pin / 1e6 * PRICE_IN_PER_MTOK + pout / 1e6 * PRICE_OUT_PER_MTOK
            usage_log.append(
                {
                    "step": step,
                    "prompt_tokens": pin,
                    "completion_tokens": pout,
                    "cost_usd": round(cost, 6),
                }
            )

        if verbose:
            names = [tc.function.name for tc in (msg.tool_calls or [])]
            print(f"[step {step}] {names or 'финал-текст'}")

        if not msg.tool_calls:
            final_event = {"step": step, "final": msg.content}
            trace.append(final_event)
            _log_trace_event(trace_path, run_id, final_event)
            return _finish(
                {
                    "answer": msg.content,
                    "structured": None,
                    "trace": trace,
                    "steps": step,
                    "run_id": run_id,
                },
                usage_log,
                track_cost=track_cost,
                use_cache=use_cache,
                verbose=verbose,
            )

        submit = next(
            (tc for tc in msg.tool_calls if tc.function.name == "submit_answer"), None
        )
        others = [tc for tc in msg.tool_calls if tc is not submit]

        # блок 6 — исполняем обычные вызовы (параллельно, если их несколько)
        if others:
            if parallel and len(others) > 1:
                with ThreadPoolExecutor(max_workers=4) as ex:
                    results = list(ex.map(lambda t: _exec_one(t, cache), others))
            else:
                results = [_exec_one(tc, cache) for tc in others]
            for tc, args, obs in results:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(obs, ensure_ascii=False),
                    }
                )
                tool_event = {
                    "step": step,
                    "call": tc.function.name,
                    "args": args,
                    "obs": obs,
                }
                trace.append(tool_event)
                _log_trace_event(trace_path, run_id, tool_event)
                if verbose:
                    print(
                        f"    {tc.function.name}({args}) -> {json.dumps(obs, ensure_ascii=False)[:140]}"
                    )

        # блок 7 + 8 — финал через submit_answer и самопроверку
        if submit is not None:
            try:
                ans = AgentAnswer(**json.loads(submit.function.arguments or "{}"))
            except Exception as e:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": submit.id,
                        "content": f"submit_answer invalid: {e}. Fix it.",
                    }
                )
                continue
            if use_critic:
                verdict = critique(ans, trace)
                if verbose:
                    print(f"    [ревизор] ok={verdict.ok} {verdict.issue}")
                if not verdict.ok:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": submit.id,
                            "content": f"Reviewer rejected: {verdict.issue}. "
                            f"Double-check and call submit_answer again.",
                        }
                    )
                    continue
            messages.append(
                {"role": "tool", "tool_call_id": submit.id, "content": "answer accepted"}
            )
            final_event = {"step": step, "final": ans.answer}
            trace.append(final_event)
            _log_trace_event(trace_path, run_id, final_event)
            return _finish(
                {
                    "answer": ans.answer,
                    "structured": ans,
                    "trace": trace,
                    "steps": step,
                    "run_id": run_id,
                },
                usage_log,
                track_cost=track_cost,
                use_cache=use_cache,
                verbose=verbose,
            )

    error_event = {
        "step": max_iter,
        "final": None,
        "error": f"исчерпан лимит шагов max_iter={max_iter}",
    }
    trace.append(error_event)
    _log_trace_event(trace_path, run_id, error_event)
    return _finish(
        {
            "answer": None,
            "structured": None,
            "trace": trace,
            "steps": max_iter,
            "error": f"исчерпан лимит шагов max_iter={max_iter}",
            "run_id": run_id,
        },
        usage_log,
        track_cost=track_cost,
        use_cache=use_cache,
        verbose=verbose,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="+", help="Вопрос к агенту")
    ap.add_argument("--max-iter", type=int, default=8)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument(
        "--parallel",
        action="store_true",
        help="блок 6: параллельные вызовы инструментов",
    )
    ap.add_argument(
        "--structured",
        action="store_true",
        help="блок 7: структурный финал через submit_answer",
    )
    ap.add_argument(
        "--critic",
        action="store_true",
        help="блок 8: самопроверка финала (нужен --structured)",
    )
    ap.add_argument(
        "--cache",
        action="store_true",
        help="блок 9: кэш детерминированных инструментов",
    )
    ap.add_argument(
        "--cost",
        action="store_true",
        help="блок 10: показать токены и стоимость по шагам",
    )
    ap.add_argument(
        "--trace",
        type=Path,
        default=TRACE_PATH,
        help="Куда писать JSONL-лог шагов (по умолчанию trace.jsonl)",
    )
    ap.add_argument(
        "--no-trace",
        action="store_true",
        help="Не писать trace.jsonl",
    )
    a = ap.parse_args()

    q = " ".join(a.query)
    res = run_agent(
        q,
        max_iter=a.max_iter,
        verbose=not a.quiet,
        parallel=a.parallel,
        structured=a.structured,
        use_critic=a.critic,
        use_cache=a.cache,
        track_cost=a.cost,
        trace_path=None if a.no_trace else a.trace,
    )

    print("\n=== ВОПРОС ===")
    print(q)
    print("\n=== ОТВЕТ ===")
    s = res.get("structured")
    if s:
        print(s.answer)
        print(
            f"value={s.value} {s.unit or ''} | sources={s.sources} | confidence={s.confidence:.2f}"
        )
    else:
        print(res.get("answer") or res.get("error"))
    print(f"\n(шагов: {res['steps']})")


if __name__ == "__main__":
    main()
