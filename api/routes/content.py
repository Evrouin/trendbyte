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
async def get_daily_content() -> dict:
    return _generator.generate_daily()


@router.get("/content/weekly")
@cached
async def get_weekly_content() -> dict:
    return _generator.generate_weekly()


@router.get("/content/monthly")
@cached
async def get_monthly_content() -> dict:
    return _generator.generate_monthly()
