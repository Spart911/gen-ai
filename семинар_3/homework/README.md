# Домашнее задание — семинар 3, вариант A

Анализ **50 отзывов** на мобильное приложение **FoodGo** (доставка еды) с помощью LLM-пайплайна.

## Что внутри

| Файл | Назначение |
|------|------------|
| `schema.py` | Pydantic-модели: отзывы, аспекты, autodiscovery, сводка, судья |
| `prompts.py` | System-промпты (на английском); ответы модели — на русском |
| `pipeline.py` | Главный конвейер `analyze()` |
| `prompt_caching.py` | Бенчмарк prompt caching (можно отдельно) |
| `generate_reviews.py` | Генератор синтетических отзывов |
| `input/` | Исходные тексты (50 отзывов) |
| `output/` | Артефакты прогона |

## Подготовка

1. Скопируйте `.env` из корня `семинар_3/` (или из `.env.example`).
2. Установи зависимости из `../starter/requirements.txt` + `seaborn`.
3. Python **3.11+**.

```bash
cd семинар_3/homework
python3.11 pipeline.py input/reviews.txt output
```

Флаг `--no-cache` пропускает шаг бенчмарка кэша (быстрее).

## Шаги пайплайна

```
input/reviews.txt
       │
       ▼
[1] IE ──────────────────────► reviews.json, reviews.csv
       │
       ▼
[2] Аспекты (фикс. список) ──► aspects.json, heatmap.png
       │
       ▼
[3] Autodiscovery ───────────► discovered_themes.json
       │                        aspects_discovered.json
       │                        aspect_discovery_report.json
       │                        heatmap_discovered.png
       ▼
[4] Map-Reduce ──────────────► summary.json
       │
       ▼
[5] LLM-as-judge ────────────► judge_report.json
       │
       ▼
[6] Prompt caching ──────────► cache_report.json
       │
       ▼
     metrics.json
```

### Базовые техники (обязательно)

- **IE** — извлечение структуры отзыва и цитат
- **Аспекты** — оценки по 6 фиксированным темам
- **Map-Reduce** — сводка по всем отзывам
- **Judge** — проверка, что рекомендации следуют из фактов

### Бонусы для «отлично»

- **Autodiscovery** — модель сама находит темы, потом классифицирует по ним; сравнение с фиксированным списком в `aspect_discovery_report.json`
- **Prompt caching** — 4 прогона с замером `prompt_cache_hit_tokens` в `cache_report.json`

## Выходные файлы

| Файл | Содержимое |
|------|------------|
| `reviews.json` | IE: автор, оценка, проблемы, цитаты |
| `aspects.json` | Аспекты по фиксированному списку |
| `discovered_themes.json` | Темы от autodiscovery |
| `aspects_discovered.json` | Аспекты по найденным темам |
| `aspect_discovery_report.json` | Сравнение fixed vs discovered |
| `summary.json` | Общая сводка и рекомендации |
| `judge_report.json` | Вердикты судьи, `overall_score` |
| `cache_report.json` | Замеры кэша и экономия |
| `metrics.json` | Сводная статистика прогона |
| `heatmap.png` | Тепловая карта (fixed) |
| `heatmap_discovered.png` | Тепловая карта (autodiscovery) |

## Отдельные команды

```bash
# Только бенчмарк кэша
python3.11 prompt_caching.py input/reviews.txt output/cache_report.json

# Перегенерировать отзывы через LLM
python3.11 generate_reviews.py

# Собрать input/ из готового JSON без API
python3.11 generate_reviews.py --offline
```

## Критерии качества

- Ghost-цитат ≤ 10% (проверка `check_quotes`)
- `overall_score` судьи ≥ 0.7 (иначе пайплайн повторяет Map-Reduce)
- Отчёт `выводы.md` — отдельно, по цифрам из `metrics.json`

## Структура данных

**Приложение:** FoodGo — доставка еды  
**Магазины:** App Store, Google Play, RuStore  
**Фиксированные аспекты:** производительность, дизайн, поддержка, цена, реклама, надёжность
