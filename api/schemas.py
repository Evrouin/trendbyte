from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TrendResponse(BaseModel):
    trends: list[dict]
    count: int


class TrendDetailResponse(BaseModel):
    trend: dict | None = None
    history: list[dict] = []
    posts: list[dict] = []
    related: list[dict] = []
    lifecycle: dict = {}
    error: str | None = None


class StatsResponse(BaseModel):
    total_mentions: int
    total_trends: int
    total_predictions: int
    active_sources: list[str]
    last_run: datetime | None


class NewsResponse(BaseModel):
    news: list[dict]
    count: int


class PredictionResponse(BaseModel):
    predictions: list[dict]
    count: int


class ContentDailyResponse(BaseModel):
    headline: str = ""
    trend_name: str = ""
    stat: dict = {}
    takeaway: str = ""
    hook: str = ""


class ContentWeeklyResponse(BaseModel):
    most_discussed: dict = {}
    rising_tool: dict = {}
    community_vibe: dict = {}
    faded: dict = {}
