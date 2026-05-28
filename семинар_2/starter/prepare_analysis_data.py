"""
Подготовка данных для 5_analysis.py и запуск анализа без правок семинарского скрипта.

Маппинг Application → Persona (только в analysis_input.json):
  name       ← full_name
  occupation ← speciality
  income_rub ← years_of_experience * 15_000   # прокси для boxplot

Запуск:
    python prepare_analysis_data.py

Результат:
    analysis_input.json
    crosstab_city_speciality.csv
    report.md          (из 5_analysis.py + блок про ДПО)
    ages.png, occupations.png, income_by_occupation.png
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

SRC = Path("applications.json")
OUT = Path("analysis_input.json")
CROSSTAB = Path("crosstab_city_speciality.csv")
REPORT = Path("report.md")
ANALYSIS_SCRIPT = Path("5_analysis.py")

# cities.png — файл из generator.py для сдачи; 5_analysis.py его перезаписывает.
CITIES_PNG_BACKUP = Path(".cities_png_backup")


def convert_applications() -> list[dict]:
    with SRC.open(encoding="utf-8") as f:
        apps = json.load(f)

    rows = []
    for app in apps:
        rows.append(
            {
                "name": app["full_name"],
                "age": app["age"],
                "address": app["address"],
                "occupation": app["speciality"],
                "income_rub": app["years_of_experience"] * 15_000,
            }
        )
    return rows


def save_crosstab(rows: list[dict]) -> pd.DataFrame:
    df = pd.json_normalize(rows)
    df["city"] = df["address.city"]
    ct = pd.crosstab(df["city"], df["occupation"])
    ct.to_csv(CROSSTAB, encoding="utf-8")
    return ct


def run_seminar_analysis() -> None:
    if Path("cities.png").exists():
        shutil.copy("cities.png", CITIES_PNG_BACKUP)
    subprocess.run(
        [sys.executable, str(ANALYSIS_SCRIPT), str(OUT)],
        check=True,
    )
    if CITIES_PNG_BACKUP.exists():
        shutil.move(CITIES_PNG_BACKUP, "cities.png")


def pick_unrealistic_combos() -> list[str]:
    """Три спорные комбинации из applications.json для блока в report.md."""
    with SRC.open(encoding="utf-8") as f:
        apps = json.load(f)

    lines: list[str] = []

    for app in apps:
        if (
            app["speciality"] == "социальный работник"
            and app["desired_course"] == "Менеджмент в образовании"
        ):
            lines.append(
                f"1. **{app['full_name']}** ({app['address']['city']}): "
                f"«{app['speciality']}» → «{app['desired_course']}». "
                f"Соцработники редко идут на управленческий курс — скорее "
                f"социально-педагогические программы."
            )
            break

    for app in apps:
        if (
            app["speciality"] == "экономист"
            and app["desired_course"] == "Бухгалтерский учёт и налогообложение"
        ):
            lines.append(
                f"2. **{app['full_name']}** ({app['address']['city']}): "
                f"«{app['speciality']}» → «{app['desired_course']}». "
                f"Формально допустимо, но выглядит как понижение профиля, "
                f"не типичный шаг для экономиста."
            )
            break

    for app in apps:
        age = int(app["age"])
        exp = int(app["years_of_experience"])
        max_exp = max(age - 22, 0)
        if exp > max_exp:
            lines.append(
                f"3. **{app['full_name']}** ({app['address']['city']}): "
                f"возраст {age}, стаж {exp} лет (макс. ~{max_exp} после вуза), "
                f"курс «{app['desired_course']}». "
                f"Pydantic пропустил — видно только при ручной проверке числовых полей."
            )
            break

    return lines


def append_dpo_section() -> None:
    combos = pick_unrealistic_combos()
    extra = [
        "",
        "---",
        "",
        "## Дополнение: заявки на ДПО",
        "",
        "Данные подготовлены из `applications.json` (`prepare_analysis_data.py`). "
        "`5_analysis.py` **не изменялся**. В JSON для совместимости: "
        "`occupation` = `speciality`, `income_rub` = `years_of_experience × 15_000`.",
        "",
        f"Кросс-таблица (CSV): `{CROSSTAB.name}`",
        "",
        "### Нереалистичные / спорные комбинации",
        "",
        "`5_analysis.py` строит кросс-таблицу **город × специальность**. "
        "Ниже — три спорных случая по парам **специальность → курс** "
        "из исходных заявок:",
        "",
    ]
    extra.extend(combos if combos else ["- Явных аномалий не найдено."])
    REPORT.write_text(REPORT.read_text(encoding="utf-8") + "\n".join(extra), encoding="utf-8")


def main() -> None:
    if not SRC.exists():
        sys.exit(f"Нет {SRC} — сначала запусти generator.py")
    if not ANALYSIS_SCRIPT.exists():
        sys.exit(f"Нет {ANALYSIS_SCRIPT}")

    rows = convert_applications()
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    save_crosstab(rows)
    print(f"Сохранено: {OUT} ({len(rows)} записей)")
    print(f"Сохранено: {CROSSTAB}")

    run_seminar_analysis()
    append_dpo_section()
    print(f"Сохранено: {REPORT} (+ блок ДПО)")
    print("\nГотово. Семинарский 5_analysis.py не менялся.")


if __name__ == "__main__":
    main()
