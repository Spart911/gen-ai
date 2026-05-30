"""
Генератор синтетических отзывов на мобильное приложение.

По образцу generator.py из семинара 2 и generate_transcripts.py из семинара 3:
  • стратификация по магазину, оценке и теме отзыва;
  • один запрос LLM → один отзыв через make_client() + Pydantic;
  • сохранение в input/reviews.txt и input/reviews/*.txt.

Запуск:
    python generate_reviews.py              # 50 отзывов через LLM (нужен .env)
    python generate_reviews.py --offline    # записать готовый reviews.txt без API

На выходе:
    input/reviews.txt       — все 50 отзывов в одном файле
    input/reviews/          — по одному .txt на отзыв
    input/reviews_raw.json  — структурированный JSON (после LLM-прогона)
"""

import argparse
import json
import random
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

# llm_client лежит в starter/ — добавим в path при запуске из homework/
_STARTER = Path(__file__).resolve().parent.parent / "starter"
if str(_STARTER) not in sys.path:
    sys.path.insert(0, str(_STARTER))

from llm_client import get_model, make_client  # noqa: E402

APP_NAME = "FoodGo"
APP_DESCRIPTION = "мобильное приложение доставки еды и продуктов"
N_REVIEWS = 50

STORES = ("App Store", "Google Play", "RuStore")
RATINGS = (1, 2, 3, 4, 5)

# Темы для стратификации — совпадают с аспектами из ДЗ
FOCUS_TOPICS = (
    "производительность",
    "дизайн",
    "поддержка",
    "цена",
    "реклама",
    "надёжность",
    "смешанный",
)

Store = Literal["App Store", "Google Play", "RuStore"]


class ReviewDraft(BaseModel):
    """Один отзыв — форма ответа для LLM."""

    author: str = Field(description="Имя или ник автора, например «Марина К.»")
    rating: int = Field(ge=1, le=5, description="Оценка от 1 до 5")
    store: Store
    review_date: date = Field(description="Дата отзыва в формате YYYY-MM-DD")
    title: Optional[str] = Field(default=None, description="Заголовок отзыва, если есть")
    body: str = Field(
        min_length=40,
        description="Текст отзыва на русском, 2–6 предложений, с конкретными деталями",
    )

    @field_validator("review_date")
    @classmethod
    def not_in_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("дата отзыва не может быть в будущем")
        return v


SYSTEM_PROMPT = f"""Ты генерируешь правдоподобные отзывы на {APP_DESCRIPTION} «{APP_NAME}» для российских
магазинов приложений. Пиши только на русском.

Правила:
  • body — живой текст от 2 до 6 предложений, с конкретикой (что именно сломалось / понравилось).
  • Не используй шаблон «всё супер» без деталей.
  • Если оценка низкая (1–2) — опиши проблему; если высокая (4–5) — что именно устроило.
  • Не выдумывай технические детали вроде «версия 9.4.2 build 8812», если их не просят.
  • author — короткое имя или ник, без email и телефона.

Верни JSON по схеме."""


@dataclass(frozen=True)
class GenerationSeed:
    rating: int
    store: Store
    focus: str
    review_date: date


def stratify(values: tuple, n: int) -> list:
    items = list(values)
    random.shuffle(items)
    per = n // len(items)
    plan: list = []
    for item in items:
        plan.extend([item] * per)
    while len(plan) < n:
        plan.append(random.choice(items))
    random.shuffle(plan)
    return plan


def build_generation_plan(n: int) -> list[GenerationSeed]:
    ratings = stratify(RATINGS, n)
    stores = stratify(STORES, n)
    focuses = stratify(FOCUS_TOPICS, n)
    base = date.today() - timedelta(days=120)
    seeds: list[GenerationSeed] = []
    for i, (rating, store, focus) in enumerate(zip(ratings, stores, focuses)):
        review_date = base + timedelta(days=random.randint(0, 119))
        seeds.append(
            GenerationSeed(
                rating=rating,
                store=store,
                focus=focus,
                review_date=review_date,
            )
        )
    random.shuffle(seeds)
    return seeds


def build_user_prompt(seed: GenerationSeed, used_authors: set[str]) -> str:
    avoid = ""
    if used_authors:
        sample = sorted(used_authors)[:15]
        avoid = f" Не повторяй этих авторов: {', '.join(sample)}."

    focus_hint = {
        "производительность": "главная тема — тормоза, вылеты, долгая загрузка, зависания.",
        "дизайн": "главная тема — интерфейс, шрифты, навигация, тёмная тема.",
        "поддержка": "главная тема — чат поддержки, оператор, возврат денег, долгий ответ.",
        "цена": "главная тема — дорогая доставка, скрытые комиссии, промокоды, скидки.",
        "реклама": "главная тема — навязчивые push, баннеры, спам-рассылки.",
        "надёжность": "главная тема — не привезли заказ, ошибка оплаты, пропал статус.",
        "смешанный": "упомяни 2–3 разных аспекта в одном отзыве.",
    }[seed.focus]

    return (
        f"Сгенерируй один отзыв.\n"
        f"- rating MUST быть ровно {seed.rating}\n"
        f"- store MUST быть ровно {seed.store!r}\n"
        f"- review_date MUST быть {seed.review_date.isoformat()}\n"
        f"- {focus_hint}{avoid}"
    )


def format_review_block(review: ReviewDraft, index: int) -> str:
    title_line = f"Заголовок: {review.title}\n" if review.title else ""
    return (
        f"{'═' * 59}\n"
        f"ОТЗЫВ #{index:03d}\n"
        f"Приложение: {APP_NAME} — {APP_DESCRIPTION}\n"
        f"Магазин: {review.store}\n"
        f"Оценка: {review.rating}/5\n"
        f"Автор: {review.author}\n"
        f"Дата: {review.review_date.isoformat()}\n"
        f"{title_line}"
        f"{'═' * 59}\n\n"
        f"{review.body.strip()}\n"
    )


def save_reviews(reviews: list[ReviewDraft], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    reviews_dir = out_dir / "reviews"
    reviews_dir.mkdir(exist_ok=True)

    blocks: list[str] = []
    for i, review in enumerate(reviews, 1):
        block = format_review_block(review, i)
        blocks.append(block)
        (reviews_dir / f"review_{i:03d}.txt").write_text(block, encoding="utf-8")

    combined = "\n".join(blocks)
    (out_dir / "reviews.txt").write_text(combined, encoding="utf-8")

    json_path = out_dir / "reviews_raw.json"
    json_path.write_text(
        json.dumps(
            [r.model_dump(mode="json") for r in reviews],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def generate_one(
    client,
    model: str,
    seed: GenerationSeed,
    used_authors: set[str],
) -> ReviewDraft:
    return client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(seed, used_authors)},
        ],
        response_model=ReviewDraft,
        max_retries=3,
        temperature=0.92,
    )


def run_llm_generation(out_dir: Path, n: int = N_REVIEWS) -> list[ReviewDraft]:
    client = make_client()
    model = get_model()
    plan = build_generation_plan(n)
    reviews: list[ReviewDraft] = []
    used_authors: set[str] = set()

    print(f"Генерация {n} отзывов через {model}...")
    for i, seed in enumerate(plan, 1):
        print(
            f"[{i}/{n}] rating={seed.rating}, store={seed.store!r}, "
            f"focus={seed.focus!r}...",
            end=" ",
            flush=True,
        )
        for attempt in range(6):
            try:
                review = generate_one(client, model, seed, used_authors)
                if review.rating != seed.rating:
                    raise ValueError(f"rating {review.rating} != {seed.rating}")
                if review.store != seed.store:
                    raise ValueError(f"store {review.store!r} != {seed.store!r}")
                if review.author in used_authors:
                    raise ValueError(f"duplicate author: {review.author!r}")
                reviews.append(review)
                used_authors.add(review.author)
                print(f"✓ {review.author!r}")
                break
            except Exception as e:
                if attempt < 5:
                    print(f"↻ {type(e).__name__}, повтор...", end=" ", flush=True)
                    time.sleep(1.2)
                else:
                    print(f"✗ {type(e).__name__}: {e}")
        time.sleep(0.25)

    save_reviews(reviews, out_dir)
    print_stats(reviews)
    return reviews


def print_stats(reviews: list[ReviewDraft]) -> None:
    n = len(reviews)
    print(f"\n── Статистика ({n} отзывов) ──")
    for label, counter in [
        ("Магазины", Counter(r.store for r in reviews)),
        ("Оценки", Counter(r.rating for r in reviews)),
    ]:
        print(f"  {label}:")
        for key, count in counter.most_common():
            print(f"    {key}: {count} ({count / n * 100:.0f}%)")


def load_offline_reviews() -> list[ReviewDraft]:
    """Готовый набор из 50 отзывов — без вызова LLM."""
    raw_path = Path(__file__).parent / "input" / "reviews_raw.json"
    if raw_path.exists():
        data = json.loads(raw_path.read_text(encoding="utf-8"))
        return [ReviewDraft.model_validate(item) for item in data]

    # Если JSON ещё нет — парсим reviews.txt (после первой записи файла)
    txt_path = Path(__file__).parent / "input" / "reviews.txt"
    if not txt_path.exists():
        raise FileNotFoundError(
            "Нет input/reviews.txt. Запусти скрипт после создания файла "
            "или используй LLM-режим без --offline."
        )
    return parse_reviews_txt(txt_path.read_text(encoding="utf-8"))


def parse_reviews_txt(text: str) -> list[ReviewDraft]:
    """Разбор reviews.txt обратно в ReviewDraft (для --offline --rebuild-json)."""
    import re

    blocks = re.split(r"═{10,}\nОТЗЫВ #\d+\n", text)
    reviews: list[ReviewDraft] = []
    for block in blocks:
        block = block.strip()
        if not block or not block.startswith("Приложение:"):
            continue
        lines = block.splitlines()
        meta: dict[str, str] = {}
        body_lines: list[str] = []
        in_body = False
        for line in lines:
            if line.startswith("═"):
                in_body = True
                continue
            if not in_body:
                if line.startswith("Магазин:"):
                    meta["store"] = line.split(":", 1)[1].strip()
                elif line.startswith("Оценка:"):
                    meta["rating"] = line.split(":", 1)[1].strip().split("/")[0]
                elif line.startswith("Автор:"):
                    meta["author"] = line.split(":", 1)[1].strip()
                elif line.startswith("Дата:"):
                    meta["date"] = line.split(":", 1)[1].strip()
                elif line.startswith("Заголовок:"):
                    meta["title"] = line.split(":", 1)[1].strip()
            else:
                if line.strip():
                    body_lines.append(line)
        if not body_lines:
            continue
        reviews.append(
            ReviewDraft(
                author=meta["author"],
                rating=int(meta["rating"]),
                store=meta["store"],  # type: ignore[arg-type]
                review_date=date.fromisoformat(meta["date"]),
                title=meta.get("title"),
                body=" ".join(body_lines),
            )
        )
    return reviews


def main() -> None:
    parser = argparse.ArgumentParser(description="Генератор отзыов FoodGo для ДЗ")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Пересобрать input/reviews/*.txt из готового reviews_raw.json или reviews.txt",
    )
    parser.add_argument(
        "-n",
        type=int,
        default=N_REVIEWS,
        help=f"Число отзывов для LLM-генерации (по умолчанию {N_REVIEWS})",
    )
    args = parser.parse_args()

    base = Path(__file__).parent
    out_dir = base / "input"

    if args.offline:
        reviews = load_offline_reviews()
        save_reviews(reviews[: args.n], out_dir)
        print(f"✓ Записано {min(len(reviews), args.n)} отзывов в {out_dir}/")
        print_stats(reviews[: args.n])
        return

    run_llm_generation(out_dir, n=args.n)
    print(f"\nСохранено:\n  {out_dir / 'reviews.txt'}\n  {out_dir / 'reviews/'}\n  {out_dir / 'reviews_raw.json'}")


if __name__ == "__main__":
    main()
