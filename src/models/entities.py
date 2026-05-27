from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class Mention:
    source: str
    name: str
    url: str
    description: str
    stars: int | None = None
    forks: int | None = None
    score: float = 0.0
    collected_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class Trend:
    name: str
    mentions: int
    growth_pct: float
    score: float
    sources: list[str] = field(default_factory=list)
    top_url: str = ""


@dataclass(frozen=True)
class Post:
    trend_name: str
    tweet_id: str
    tweet_text: str
    image_path: str | None = None
    posted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
