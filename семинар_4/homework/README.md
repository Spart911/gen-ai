# Домашнее задание — семинар 4

RAG по корпусу **12 документов** ru.stackoverflow.com (`data/doc_*_ru_*.md`).

## Подготовка

```bash
cd семинар_4/homework
# .env с LLM_BASE_URL / LLM_AUTH_TOKEN / LLM_MODEL — из семинар_4/starter или корня репо
pip install -r ../starter/requirements.txt
```

## RAG-пайплайн

```bash
# Индексация (обе стратегии — для сравнения в eval)
python pipeline.py ingest --strategy fixed
python pipeline.py ingest --strategy recursive

# Вопрос
python pipeline.py ask "Что передавать в messages для контекста?" --strategy recursive

# Eval hit-rate@5
python eval.py --strategy fixed
python eval.py --strategy recursive
python eval.py --compare          # → eval_results.json, chunking_comparison.json
```

Сравнение стратегий чанкинга — см. **`chunking_comparison.md`**.  
Полный отчёт по ДЗ — **`отчёт.md`**.

## Стратегии чанкинга

| Стратегия | Описание |
|-----------|----------|
| `fixed` | `text[i:i+2000]`, без перекрытия |
| `recursive` | `RecursiveCharacterTextSplitter(400, overlap=80)` по заголовкам и абзацам |

Поиск: ChromaDB (dense) + BM25 + RRF. Ответ: structured `RAGAnswer` через `make_client()`.
