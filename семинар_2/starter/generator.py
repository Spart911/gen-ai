"""
Генератор синтетических заявок на курсы повышения квалификации (ДПО).

Запуск:
    python generator.py

На выходе:
    applications.json  — сырые данные
    applications.csv   — таблица с распакованным address
    cities.png         — гистограмма по городам
    specialities.png   — гистограмма по специальностям
"""

from __future__ import annotations

import csv
import json
import random
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from llm_client import get_model, make_client
from schema import (
    CITIES,
    COURSES,
    SPECIALITIES,
    SPECIALITY_COURSE_MAP,
    Application,
)

client = make_client()
MODEL = get_model()

N_APPLICATIONS = 50

SEED_SURNAMES = (
    "Kozlov",
    "Novikov",
    "Morozov",
    "Volkov",
    "Sokolov",
    "Lebedev",
    "Kuznetsov",
    "Popov",
    "Vasiliev",
    "Fedorov",
    "Mikhailov",
    "Belov",
    "Komarov",
    "Orlov",
    "Zaitsev",
    "Egorov",
    "Pavlov",
    "Semenov",
    "Golubev",
    "Vinogradov",
)

SYSTEM_PROMPT = """You generate synthetic applications for professional
development (continuing education) courses in Russia. Create a plausible
application: provide full name, age (22–65), address (city and district),
current speciality, desired course, years of work experience (0–40), and
university graduation year (1980–2024).

The graduation year must be consistent with age: the applicant cannot have
graduated later than (age − 22) years ago from the current year.

Allowed specialities (use these exact Russian strings):
  учитель начальных классов, воспитатель, логопед, психолог, медсестра,
  инженер, бухгалтер, юрист, социальный работник, экономист.

Allowed courses (use these exact Russian strings):
  Педагогика и методика начального образования,
  Коррекционная педагогика,
  Менеджмент в образовании,
  Информационные технологии в образовании,
  Дошкольная педагогика,
  Медицинское дело,
  Бухгалтерский учёт и налогообложение,
  Правовое обеспечение.

Return the response as JSON."""


@dataclass(frozen=True)
class GenerationSeed:
    city: str
    speciality: str
    course: str
    surname_hint: str


def stratify(values: tuple[str, ...], n: int) -> list[str]:
    """Even quota per category, remainder distributed randomly, then shuffled."""
    items = list(values)
    random.shuffle(items)
    per = n // len(items)
    plan: list[str] = []
    for item in items:
        plan.extend([item] * per)
    while len(plan) < n:
        plan.append(random.choice(items))
    random.shuffle(plan)
    return plan


def pick_course_for_speciality(speciality: str, course_counts: Counter) -> str:
    """Pick the least-used plausible course for this speciality."""
    options = SPECIALITY_COURSE_MAP[speciality]
    return min(options, key=lambda c: course_counts[c])


def build_generation_plan(n: int) -> list[GenerationSeed]:
    """
    Full stratification: cities + specialities + plausible courses + surname hints.
    50 apps → 5 per speciality, ~4 per city, balanced courses via mapping.
    """
    cities = stratify(tuple(CITIES), n)
    specialities = stratify(SPECIALITIES, n)
    course_counts: Counter = Counter({c: 0 for c in COURSES})
    surnames = stratify(SEED_SURNAMES, n)

    seeds: list[GenerationSeed] = []
    for city, speciality, surname_hint in zip(cities, specialities, surnames):
        course = pick_course_for_speciality(speciality, course_counts)
        course_counts[course] += 1
        seeds.append(
            GenerationSeed(
                city=city,
                speciality=speciality,
                course=course,
                surname_hint=surname_hint,
            )
        )
    random.shuffle(seeds)
    return seeds


def build_user_prompt(seed: GenerationSeed, used_names: set[str]) -> str:
    avoid = ""
    if used_names:
        sample = sorted(used_names)[:20]
        avoid = f" Do NOT reuse these full names: {', '.join(sample)}."

    return (
        f"Create one application.\n"
        f"- address.city MUST be {seed.city!r}; set a realistic district "
        f"of that city in address.district.\n"
        f"- speciality MUST be exactly {seed.speciality!r}.\n"
        f"- desired_course MUST be exactly {seed.course!r}.\n"
        f"- full_name MUST be a unique realistic Russian full name "
        f"(surname, first name, patronymic). Prefer surname similar to "
        f"«{seed.surname_hint}» transliterated into Cyrillic "
        f"(e.g. Kozlov → Козлов). Avoid overused surnames Ivanov/Ivanova, "
        f"Petrov/Petrova, Smirnov/Smirnova unless truly necessary.{avoid}"
    )


def generate_one(seed: GenerationSeed, used_names: set[str]) -> Application:
    return client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(seed, used_names)},
        ],
        response_model=Application,
        max_retries=3,
        temperature=0.95,
    )


def save_csv(applications: list[Application], path: Path) -> None:
    fieldnames = [
        "full_name",
        "age",
        "city",
        "district",
        "speciality",
        "desired_course",
        "years_of_experience",
        "graduation_year",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for app in applications:
            writer.writerow(
                {
                    "full_name": app.full_name,
                    "age": app.age,
                    "city": app.address.city,
                    "district": app.address.district,
                    "speciality": app.speciality,
                    "desired_course": app.desired_course,
                    "years_of_experience": app.years_of_experience,
                    "graduation_year": app.graduation_year,
                }
            )


def plot_bar(series: pd.Series, title: str, out: Path, color: str = "#4A90D9") -> None:
    counts = series.value_counts()
    plt.figure(figsize=(10, 5))
    counts.plot.bar(color=color, edgecolor="white")
    plt.title(title)
    plt.ylabel("Число заявок")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()


def print_stats(df: pd.DataFrame) -> None:
    n = len(df)
    print(f"\n── Статистика ({n} заявок) ──")
    for col, threshold in [
        ("city", 40),
        ("speciality", 35),
        ("desired_course", 35),
    ]:
        counts = df[col].value_counts()
        top = counts.index[0]
        pct = counts.iloc[0] / n * 100
        status = "✓" if pct <= threshold else "⚠"
        print(f"  {status} {col}: топ «{top}» — {counts.iloc[0]} ({pct:.0f}%), порог {threshold}%")
    unique_names = df["full_name"].nunique()
    dup_rate = (1 - unique_names / n) * 100
    status = "✓" if unique_names >= n * 0.8 else "⚠"
    print(f"  {status} Уникальных ФИО: {unique_names} из {n} (дубликатов {dup_rate:.0f}%)")


def main() -> None:
    base = Path(__file__).parent
    plan = build_generation_plan(N_APPLICATIONS)
    applications: list[Application] = []
    used_names: set[str] = set()

    print(
        f"Генерация {N_APPLICATIONS} заявок "
        f"(стратификация: {len(CITIES)} городов × {len(SPECIALITIES)} специальностей)..."
    )
    for i, seed in enumerate(plan, 1):
        print(
            f"[{i}/{N_APPLICATIONS}] city={seed.city!r}, "
            f"spec={seed.speciality!r}...",
            end=" ",
            flush=True,
        )
        for attempt in range(8):
            try:
                app = generate_one(seed, used_names)
                if app.full_name in used_names:
                    raise ValueError(f"duplicate full_name: {app.full_name!r}")
                if app.speciality != seed.speciality:
                    raise ValueError(
                        f"wrong speciality: {app.speciality!r} != {seed.speciality!r}"
                    )
                if app.desired_course != seed.course:
                    raise ValueError(
                        f"wrong course: {app.desired_course!r} != {seed.course!r}"
                    )
                if app.address.city != seed.city:
                    raise ValueError(
                        f"wrong city: {app.address.city!r} != {seed.city!r}"
                    )
                applications.append(app)
                used_names.add(app.full_name)
                print(f"✓ {app.full_name!r} → {app.desired_course!r}")
                break
            except Exception as e:
                if attempt < 7:
                    print(f"↻ {type(e).__name__}, повтор...", end=" ", flush=True)
                    time.sleep(1.5)
                else:
                    print(f"✗ {type(e).__name__}: {e}")
        time.sleep(0.3)

    print(f"\nСгенерировано: {len(applications)} из {N_APPLICATIONS}")

    json_path = base / "applications.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(
            [a.model_dump(mode="json") for a in applications],
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"Сохранено: {json_path.name}")

    csv_path = base / "applications.csv"
    save_csv(applications, csv_path)
    print(f"Сохранено: {csv_path.name}")

    df = pd.read_csv(csv_path)
    plot_bar(df["city"], f"Распределение заявок по городам (n={len(df)})", base / "cities.png")
    plot_bar(
        df["speciality"],
        f"Распределение заявок по специальностям (n={len(df)})",
        base / "specialities.png",
        color="#E07A5F",
    )
    print("Сохранено: cities.png, specialities.png")
    print_stats(df)


if __name__ == "__main__":
    main()
