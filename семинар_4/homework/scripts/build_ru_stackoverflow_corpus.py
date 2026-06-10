#!/usr/bin/env python3
"""Сборка русскоязычного корпуса из выгрузки Stack Exchange API."""

from __future__ import annotations

import datetime as dt
import html
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
QUESTIONS_JSON = Path("/private/tmp/ru_selected_questions.json")
ANSWERS_JSON = Path("/private/tmp/ru_selected_answers.json")

DOCS = [
    {
        "doc_id": "doc_01_ru_openai_context_memory",
        "title": "ChatGPT API: контекст, память диалога и зацикливание ответов",
        "question_ids": [1517104, 1532792, 1564968, 1558305],
    },
    {
        "doc_id": "doc_02_ru_chatgpt_bot_streaming",
        "title": "ChatGPT в Telegram-ботах: скорость ответа, печать по буквам и асинхронность",
        "question_ids": [1496647, 1544586, 1541585],
    },
    {
        "doc_id": "doc_03_ru_openai_tools_rag_prompts",
        "title": "OpenAI API: function calling, поиск по документу, DALL-E и база знаний",
        "question_ids": [1591215, 1544689, 1608629, 1552863],
    },
    {
        "doc_id": "doc_04_ru_llm_hardware_vision",
        "title": "LLM-модели: выбор железа и GPT Vision в Telegram-боте",
        "question_ids": [1606069, 1598260],
    },
    {
        "doc_id": "doc_05_ru_ml_learning_resources",
        "title": "Книги и учебные ресурсы по машинному обучению",
        "question_ids": [678970],
    },
    {
        "doc_id": "doc_06_ru_neural_network_1d_array",
        "title": "Нейросеть для обработки одномерного массива",
        "question_ids": [500809],
    },
    {
        "doc_id": "doc_07_ru_sentiment_classifier_comparison",
        "title": "Сравнение классификаторов для тональной оценки комментариев",
        "question_ids": [792931],
    },
    {
        "doc_id": "doc_08_ru_pandas_no_loops",
        "title": "Как отучиться использовать циклы в Pandas",
        "question_ids": [980705],
    },
    {
        "doc_id": "doc_09_ru_pandas_consecutive_values",
        "title": "Подсчёт одинаковых значений, идущих подряд, в Pandas",
        "question_ids": [1198455],
    },
    {
        "doc_id": "doc_10_ru_pandas_rolling_average",
        "title": "Вычисление скользящего среднего в Pandas",
        "question_ids": [922246],
    },
    {
        "doc_id": "doc_11_ru_pandas_count_until_value",
        "title": "Подсчёт количества элементов до заданного значения в Pandas",
        "question_ids": [1256558],
    },
    {
        "doc_id": "doc_12_ru_sklearn_validation_regression",
        "title": "sklearn: train_test_split, отбор признаков и доверительные интервалы регрессии",
        "question_ids": [1108047, 908839, 1283898],
    },
]


def strip_html(raw: str) -> str:
    """Преобразует HTML тела Stack Overflow в читаемый Markdown-like текст."""
    raw = re.sub(
        r"<pre[^>]*><code>(.*?)</code></pre>",
        lambda match: "\n\nБлок кода:\n\n" + html.unescape(match.group(1)).strip() + "\n\n",
        raw,
        flags=re.IGNORECASE | re.DOTALL,
    )
    replacements = {
        r"</p>": "\n\n",
        r"<br\s*/?>": "\n",
        r"</li>": "\n",
        r"<li[^>]*>": "- ",
        r"</ul>|</ol>": "\n",
        r"</blockquote>": "\n\n",
        r"<blockquote[^>]*>": "\nЦитата: ",
        r"</h\d>": "\n\n",
    }
    for pattern, repl in replacements.items():
        raw = re.sub(pattern, repl, raw, flags=re.IGNORECASE)
    raw = re.sub(
        r"<code[^>]*>(.*?)</code>",
        lambda match: "`" + html.unescape(match.group(1)) + "`",
        raw,
        flags=re.DOTALL,
    )
    raw = re.sub(
        r"<a\s+[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>",
        lambda match: f"{match.group(2)} ({match.group(1)})",
        raw,
        flags=re.DOTALL,
    )
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


def owner_name(item: dict) -> str:
    owner = item.get("owner", {})
    name = html.unescape(owner.get("display_name", "неизвестный автор"))
    link = owner.get("link")
    return f"{name} ({link})" if link else name


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w#+.-]+\b", text, flags=re.UNICODE))


def section_for_question(question: dict, answers: list[dict]) -> str:
    title = html.unescape(question["title"])
    tags = ", ".join(question.get("tags", []))
    parts = [
        f"## Тред: {title}",
        "",
        f"- question_id: {question['question_id']}",
        f"- URL: {question['link']}",
        f"- Теги: {tags}",
        f"- Автор вопроса: {owner_name(question)}",
        f"- Рейтинг вопроса: {question.get('score', 0)}",
        f"- Ответов в исходном треде: {question.get('answer_count', 0)}",
        f"- Лицензия: {question.get('content_license', 'CC BY-SA 4.0')}",
        "",
        "### Вопрос",
        "",
        strip_html(question.get("body", "")),
        "",
    ]
    for answer in answers:
        accepted = "да" if answer.get("is_accepted") else "нет"
        parts.extend(
            [
                f"### Ответ {answer['answer_id']}",
                "",
                f"- Автор ответа: {owner_name(answer)}",
                f"- Рейтинг ответа: {answer.get('score', 0)}",
                f"- Принят: {accepted}",
                f"- URL ответа: https://ru.stackoverflow.com/a/{answer['answer_id']}",
                f"- Лицензия: {answer.get('content_license', 'CC BY-SA 4.0')}",
                "",
                strip_html(answer.get("body", "")),
                "",
            ]
        )
    return "\n".join(parts)


def main() -> None:
    if not QUESTIONS_JSON.exists() or not ANSWERS_JSON.exists():
        raise SystemExit(
            "Не найдены /private/tmp/ru_selected_questions.json и "
            "/private/tmp/ru_selected_answers.json. Сначала скачайте выбранные "
            "ru.stackoverflow треды через Stack Exchange API."
        )

    questions = {
        item["question_id"]: item
        for item in json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))["items"]
    }
    answers_by_question: dict[int, list[dict]] = defaultdict(list)
    for answer in json.loads(ANSWERS_JSON.read_text(encoding="utf-8"))["items"]:
        answers_by_question[answer["question_id"]].append(answer)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in DATA_DIR.glob("*.md"):
        old_file.unlink()

    sources = []
    stats = []
    today = dt.date.today().isoformat()

    for order, doc in enumerate(DOCS, start=1):
        doc_questions = [questions[question_id] for question_id in doc["question_ids"]]
        sections = []
        source_items = []

        for question in doc_questions:
            answers = sorted(
                answers_by_question[question["question_id"]],
                key=lambda item: (item.get("is_accepted", False), item.get("score", 0)),
                reverse=True,
            )[:8]
            sections.append(section_for_question(question, answers))
            source_items.append(
                {
                    "question_id": question["question_id"],
                    "title": html.unescape(question["title"]),
                    "url": question["link"],
                    "tags": question.get("tags", []),
                    "license": question.get("content_license", "CC BY-SA 4.0"),
                    "question_author": owner_name(question),
                    "answer_ids": [answer["answer_id"] for answer in answers],
                    "answer_authors": [owner_name(answer) for answer in answers],
                }
            )

        text = "\n".join(
            [
                f"# {doc['title']}",
                "",
                f"- doc_id: {doc['doc_id']}",
                "- Источник: ru.stackoverflow.com через Stack Exchange API",
                f"- Тредов внутри документа: {len(doc_questions)}",
                f"- Дата выгрузки: {today}",
                "- Лицензия исходного контента: CC BY-SA 4.0",
                "",
                *sections,
            ]
        ).strip() + "\n"

        output_path = DATA_DIR / f"{doc['doc_id']}.md"
        output_path.write_text(text, encoding="utf-8")

        sources.append(
            {
                "doc_id": doc["doc_id"],
                "order": order,
                "title": doc["title"],
                "site": "ru.stackoverflow.com",
                "sources": source_items,
            }
        )
        stats.append(
            {
                "doc_id": doc["doc_id"],
                "file": str(output_path.relative_to(ROOT)),
                "title": doc["title"],
                "chars": len(text),
                "words": word_count(text),
                "threads_in_doc": len(doc_questions),
            }
        )

    (ROOT / "sources.json").write_text(
        json.dumps(sources, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (ROOT / "corpus_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Записано документов: {len(DOCS)}")
    print(f"Папка: {DATA_DIR}")
    print(f"Всего символов: {sum(item['chars'] for item in stats)}")
    print(f"Всего слов: {sum(item['words'] for item in stats)}")
    for item in stats:
        print(f"- {item['doc_id']}: {item['chars']} символов, {item['words']} слов")


if __name__ == "__main__":
    main()
