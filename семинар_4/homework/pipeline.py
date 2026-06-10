from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi

_HOMEWORK = Path(__file__).resolve().parent
_STARTER = _HOMEWORK.parent / "starter"
if str(_STARTER) not in sys.path:
    sys.path.insert(0, str(_STARTER))

from llm_client import get_model, make_client  # noqa: E402

from schema import RAGAnswer  # noqa: E402

_llm_client = None
MODEL = get_model()

DATA_DIR = _HOMEWORK / "data"
CORPUS_GLOB = "doc_*_ru_*.md"
CHROMA_DIR = _HOMEWORK / "chroma_db"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

STRATEGIES = ("fixed", "recursive")

RECURSIVE_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=80,
    separators=["\n### ", "\n## ", "\n\n", "\n", ". ", "? ", "! ", " "],
)

_chroma: chromadb.PersistentClient | None = None
_embed_fn: embedding_functions.SentenceTransformerEmbeddingFunction | None = None
_collections: dict[str, chromadb.Collection] = {}


def _ensure_embedder() -> embedding_functions.SentenceTransformerEmbeddingFunction:
    global _embed_fn
    if _embed_fn is None:
        print("Загружаю эмбеддер...", flush=True)
        t0 = time.time()
        _embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL,
        )
        print(f"Эмбеддер готов за {time.time() - t0:.1f}с", flush=True)
    return _embed_fn


def _chroma_client() -> chromadb.PersistentClient:
    global _chroma
    if _chroma is None:
        _chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _chroma


def collection_name(strategy: str) -> str:
    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of {STRATEGIES}, got {strategy!r}")
    return f"ru_stackoverflow_{strategy}"


def bm25_cache_path(strategy: str) -> Path:
    return _HOMEWORK / f"bm25_cache_{strategy}.json"


def get_collection(strategy: str = "recursive") -> chromadb.Collection:
    if strategy not in _collections:
        _collections[strategy] = _chroma_client().get_or_create_collection(
            name=collection_name(strategy),
            embedding_function=_ensure_embedder(),
            metadata={"hnsw:space": "cosine"},
        )
    return _collections[strategy]


def _llm():
    global _llm_client
    if _llm_client is None:
        _llm_client = make_client()
    return _llm_client


def corpus_files() -> list[Path]:
    files = sorted(DATA_DIR.glob(CORPUS_GLOB))
    if not files:
        raise FileNotFoundError(
            f"Корпус не найден: {DATA_DIR / CORPUS_GLOB}. "
            "Сначала соберите doc_*_ru_*.md в data/."
        )
    return files


def tokenize_ru(text: str) -> list[str]:
    return re.findall(r"[а-яa-z0-9ё-]{2,}", text.lower())


def chunk_text_fixed(text: str, chunk_size: int = 2000) -> list[str]:
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size) if text[i : i + chunk_size].strip()]


def chunk_text_recursive(text: str) -> list[str]:
    return [c.strip() for c in RECURSIVE_SPLITTER.split_text(text) if c.strip()]


def chunk_document(text: str, strategy: str) -> list[str]:
    if strategy == "fixed":
        return chunk_text_fixed(text)
    if strategy == "recursive":
        return chunk_text_recursive(text)
    raise ValueError(f"Unknown strategy: {strategy}")


def ingest(strategy: str = "recursive") -> int:
    col = get_collection(strategy)
    existing = col.get()
    if existing["ids"]:
        col.delete(ids=existing["ids"])

    all_chunks: list[str] = []
    all_ids: list[str] = []
    all_meta: list[dict] = []

    for path in corpus_files():
        text = path.read_text(encoding="utf-8")
        chunks = chunk_document(text, strategy)
        source_id = path.stem

        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{source_id}__{i}")
            all_meta.append({"source": source_id, "chunk_id": i, "strategy": strategy})

        print(f"  {source_id}: {len(chunks)} чанков")

    col.add(documents=all_chunks, ids=all_ids, metadatas=all_meta)

    cache = {
        "strategy": strategy,
        "ids": all_ids,
        "tokens": [tokenize_ru(c) for c in all_chunks],
        "texts": all_chunks,
    }
    bm25_cache_path(strategy).write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    total = col.count()
    print(
        f"\nИндексировано [{strategy}]: {total} чанков из {len(corpus_files())} документов"
    )
    print(f"BM25-кэш: {bm25_cache_path(strategy).name}")
    return total


def _load_bm25(strategy: str) -> tuple[BM25Okapi, list[str], list[str]]:
    cache_path = bm25_cache_path(strategy)
    if not cache_path.exists():
        raise FileNotFoundError(
            f"BM25-кэш не найден ({cache_path.name}). Запустите: python pipeline.py ingest --strategy {strategy}"
        )
    data = json.loads(cache_path.read_text(encoding="utf-8"))
    return BM25Okapi(data["tokens"]), data["ids"], data["texts"]


def retrieve(query: str, k: int = 5, strategy: str = "recursive") -> dict:
    col = get_collection(strategy)
    return col.query(query_texts=[query], n_results=k)


def hybrid_retrieve(
    query: str,
    k: int = 5,
    top: int = 15,
    c: int = 60,
    strategy: str = "recursive",
) -> dict:
    col = get_collection(strategy)
    dense = col.query(query_texts=[query], n_results=top)
    dense_ids = dense["ids"][0]

    bm25, bm25_ids, bm25_texts = _load_bm25(strategy)
    tokens = tokenize_ru(query)
    scores = bm25.get_scores(tokens)
    bm25_order = sorted(range(len(bm25_ids)), key=lambda i: scores[i], reverse=True)[:top]
    sparse_ids = [bm25_ids[i] for i in bm25_order]

    rrf: dict[str, float] = {}
    for rank, cid in enumerate(dense_ids):
        rrf[cid] = rrf.get(cid, 0.0) + 1.0 / (c + rank)
    for rank, cid in enumerate(sparse_ids):
        rrf[cid] = rrf.get(cid, 0.0) + 1.0 / (c + rank)

    ordered = sorted(rrf.items(), key=lambda kv: kv[1], reverse=True)[:k]
    top_ids = [cid for cid, _ in ordered]

    text_by_id = dict(zip(bm25_ids, bm25_texts))
    for i, did in enumerate(dense["ids"][0]):
        text_by_id[did] = dense["documents"][0][i]

    return {"ids": [top_ids], "documents": [[text_by_id[i] for i in top_ids]]}


def build_prompt(query: str, hits: dict) -> str:
    docs = hits["documents"][0]
    ids = hits["ids"][0]
    ctx = "\n\n---\n\n".join(f"[{cid}]\n{text}" for cid, text in zip(ids, docs))
    return (
        "Ты отвечаешь на вопрос по архиву технических обсуждений ru.stackoverflow.com "
        "(Python, OpenAI API, pandas, sklearn и смежные темы).\n\n"
        "Правила:\n"
        "1. Опирайся ТОЛЬКО на контекст ниже. Не добавляй факты из общего знания.\n"
        "2. Если в контексте нет ответа — скажи об этом прямо.\n"
        "3. В quotes — 1–5 коротких цитат из контекста (не пересказ).\n"
        "4. В sources — id блоков, откуда взяты цитаты (формат: doc_01_ru_...__0).\n"
        "5. В confidence — 0.9+ только при прямом ответе в контексте, "
        "0.5–0.8 если собран из нескольких кусков, <0.5 если контекст не покрывает вопрос.\n\n"
        f"Контекст:\n{ctx}\n\n"
        f"Вопрос: {query}\n\n"
        "Ответ:"
    )


def ask(query: str, strategy: str = "recursive", k: int = 5) -> RAGAnswer:
    print(f"Поиск по базе [{strategy}]...", flush=True)
    t0 = time.time()
    hits = hybrid_retrieve(query, k=k, strategy=strategy)
    found = hits["ids"][0]
    print(
        f"   нашёл {len(found)} чанков за {time.time() - t0:.1f}с: {', '.join(found)}",
        flush=True,
    )

    print("Генерация ответа...", flush=True)
    t1 = time.time()
    prompt = build_prompt(query, hits)
    resp: RAGAnswer = _llm().chat.completions.create(
        model=MODEL,
        response_model=RAGAnswer,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_retries=2,
    )
    print(f"   ответ за {time.time() - t1:.1f}с", flush=True)

    print("\n" + "=" * 60)
    print(f"ВОПРОС: {query}")
    print("=" * 60)
    print(resp)
    print("\n--- источники ---")
    for cid in found:
        print(f"  {cid}")
    return resp


def _parse_args(argv: list[str]) -> tuple[str, str, str | None, int]:
    if len(argv) < 2:
        raise SystemExit(
            "Использование:\n"
            "  python pipeline.py ingest [--strategy fixed|recursive]\n"
            '  python pipeline.py ask "вопрос" [--strategy fixed|recursive]'
        )

    cmd = argv[1]
    strategy = "recursive"
    query: str | None = None
    k = 5

    i = 2
    while i < len(argv):
        arg = argv[i]
        if arg == "--strategy" and i + 1 < len(argv):
            strategy = argv[i + 1]
            i += 2
        elif arg == "--k" and i + 1 < len(argv):
            k = int(argv[i + 1])
            i += 2
        elif cmd == "ask" and query is None and not arg.startswith("--"):
            query = arg
            i += 1
        else:
            i += 1

    if strategy not in STRATEGIES:
        raise SystemExit(f"--strategy must be one of {STRATEGIES}")
    return cmd, strategy, query, k


def main() -> None:
    cmd, strategy, query, k = _parse_args(sys.argv)

    if cmd == "ingest":
        ingest(strategy)
    elif cmd == "ask":
        if not query:
            raise SystemExit('Нужен вопрос: python pipeline.py ask "..." [--strategy recursive]')
        if get_collection(strategy).count() == 0:
            raise SystemExit(
                f"Коллекция пустая. Запустите: python pipeline.py ingest --strategy {strategy}"
            )
        ask(query, strategy=strategy, k=k)
    else:
        raise SystemExit(f"Неизвестная команда: {cmd}")


if __name__ == "__main__":
    main()
