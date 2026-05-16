"""Domain entities for TrendByte."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Mention:
    """A single mention of a technology from a data source."""

    source: str
    name: str
    url: str
    description: str
    stars: int | None = None
    forks: int | None = None
    score: float = 0.0
    collected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class Trend:
    """An aggregated trend across sources."""

    name: str
    mentions: int
    growth_pct: float
    score: float
    sources: list[str] = field(default_factory=list)
    top_url: str = ""


@dataclass(frozen=True)
class Post:
    """A record of a published tweet."""

    trend_name: str
    tweet_id: str
    tweet_text: str
    image_path: str | None = None
    posted_at: datetime = field(default_factory=datetime.utcnow)
