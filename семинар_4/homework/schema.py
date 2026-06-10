from pydantic import BaseModel, Field


class RAGAnswer(BaseModel):
    answer: str = Field(description="Итоговый ответ на вопрос по архиву ru.stackoverflow.com")
    quotes: list[str] = Field(
        min_length=1,
        max_length=5,
        description="1–5 коротких цитат из контекста (не пересказ)",
    )
    confidence: float = Field(
        ge=0,
        le=1,
        description="Уверенность: 0.9+ — прямой ответ в контексте, <0.5 — контекст не покрывает вопрос",
    )
    sources: list[str] = Field(
        description="ID чанков-источников, например doc_01_ru_openai_context_memory__3",
    )
