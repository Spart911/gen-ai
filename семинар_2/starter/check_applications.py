"""
Проверка applications.json против схемы Application.
"""

import json
import sys
from collections import Counter

from pydantic import ValidationError

from schema import Application


def main(path: str = "applications.json") -> None:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"✗ Файл {path} не найден. Сначала запусти generator.py")
        return

    valid, invalid = 0, 0
    cities: Counter = Counter()
    specialities: Counter = Counter()

    for i, item in enumerate(data, 1):
        try:
            app = Application(**item)
            valid += 1
            cities[app.city] += 1
            specialities[app.speciality] += 1
        except ValidationError as e:
            invalid += 1
            for err in e.errors():
                loc = ".".join(str(x) for x in err["loc"])
                print(f"  #{i} ✗ {loc}: {err['msg']}")

    total = valid + invalid
    print(f"\n── Сводка ──")
    print(f"Всего:      {total}")
    print(f"Валидных:   {valid}")
    print(f"С ошибками: {invalid}")

    if valid > 0:
        n = valid
        print(f"\n── Разнообразие ──")
        print(f"Города: {dict(cities)}")
        top_city_pct = cities.most_common(1)[0][1] / n * 100
        print(f"  Топ-город: {top_city_pct:.0f}% (порог 40%)")
        print(f"Специальности: {dict(specialities)}")
        top_spec_pct = specialities.most_common(1)[0][1] / n * 100
        print(f"  Топ-спец.: {top_spec_pct:.0f}% (порог 35%)")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "applications.json"
    main(path)
