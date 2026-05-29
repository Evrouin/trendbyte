from __future__ import annotations

from fastapi import APIRouter

from api.cache import cached_content
from src.content.generator import ContentGenerator
from src.infra.config import Config

router = APIRouter(tags=["content"])

_config = Config.from_env()
_generator = ContentGenerator(_config.database_url)


@router.get("/content/daily")
@cached_content
async def get_daily_content() -> dict:
    return _generator.generate_daily()


@router.get("/content/weekly")
@cached_content
async def get_weekly_content() -> dict:
    return _generator.generate_weekly()


@router.get("/content/monthly")
@cached_content
async def get_monthly_content() -> dict:
    return _generator.generate_monthly()
