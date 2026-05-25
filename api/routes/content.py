"""Content generation API endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from api.cache import cached
from src.config import Config
from src.content import ContentGenerator

router = APIRouter(tags=["content"])

_config = Config.from_env()
_generator = ContentGenerator(_config.database_url)


@router.get("/content/daily")
@cached
def get_daily_content() -> dict:
    """Generate daily content summary."""
    return _generator.generate_daily()


@router.get("/content/weekly")
@cached
def get_weekly_content() -> dict:
    """Generate weekly content summary."""
    return _generator.generate_weekly()


@router.get("/content/monthly")
@cached
def get_monthly_content() -> dict:
    """Generate monthly content summary."""
    return _generator.generate_monthly()
