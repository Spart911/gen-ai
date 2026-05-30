"""
Pydantic-модели пайплайна анализа отзывов FoodGo.
"""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

Store = Literal["App Store", "Google Play", "RuStore"]
IssueCategory = Literal[
    "performance",
    "design",
    "support",
    "price",
    "ads",
    "reliability",
    "other",
]
Aspect = Literal[
    "производительность",
    "дизайн",
    "поддержка",
    "цена",
    "реклама",
    "надёжность",
]
Sentiment = Literal["positive", "negative", "neutral"]
SupportVerdict = Literal["supported", "weakly_supported", "not_supported"]

# Фиксированный список аспектов для «обычного» аспектного анализа
ASPECTS: tuple[Aspect, ...] = (
    "производительность",
    "дизайн",
    "поддержка",
    "цена",
    "реклама",
    "надёжность",
)


class Issue(BaseModel):
    """Одна проблема или похвала в отзыве."""

    category: IssueCategory
    description: str = Field(min_length=5, description="Краткий пересказ на русском")
    quote: str = Field(min_length=10, description="Точная подстрока из текста отзыва")


class Review(BaseModel):
    """Структурированный отзыв после IE."""

    author: str
    rating: int = Field(ge=1, le=5)
    store: Store
    review_date: date
    title: Optional[str] = None
    issues: list[Issue] = Field(default_factory=list)

    @field_validator("review_date")
    @classmethod
    def not_in_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("дата отзыва не может быть в будущем")
        return v


class AspectSentiment(BaseModel):
    aspect: Aspect
    sentiment: Sentiment
    confidence: float = Field(ge=0.0, le=1.0)
    quote: str = Field(min_length=10)


class ReviewSentiment(BaseModel):
    author: str
    aspects: list[AspectSentiment]


class DiscoveredAspect(BaseModel):
    """Одна тема, найденная autodiscovery (стадия A)."""

    name: str = Field(min_length=2, description="Короткая русская метка, напр. «скорость доставки»")
    description: str = Field(min_length=5, description="Одно предложение на русском")


class DiscoveredAspects(BaseModel):
    """5–10 тем, которые модель нашла в корпусе (выход стадии A)."""

    aspects: list[DiscoveredAspect] = Field(min_length=5, max_length=10)


class DynamicAspectSentiment(BaseModel):
    """Аспект из autodiscovery — строка, не фиксированный Literal."""

    aspect: str = Field(min_length=2)
    sentiment: Sentiment
    confidence: float = Field(ge=0.0, le=1.0)
    quote: str = Field(min_length=10)


class DynamicReviewSentiment(BaseModel):
    author: str
    aspects: list[DynamicAspectSentiment]


class ChunkSummary(BaseModel):
    author: str
    rating: int = Field(ge=1, le=5)
    key_points: list[str] = Field(min_length=1)
    sentiment: Sentiment


class ReviewsSummary(BaseModel):
    headline: str
    key_findings: list[str] = Field(min_length=1)
    action_items: list[str] = Field(min_length=1)


class ActionVerdict(BaseModel):
    action: str
    support: SupportVerdict
    evidence: list[str] = Field(default_factory=list)
    comment: str


class JudgeReport(BaseModel):
    verdicts: list[ActionVerdict]
    overall_score: float = Field(ge=0.0, le=1.0)
    summary: str
