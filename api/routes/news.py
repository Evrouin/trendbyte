from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from psycopg import AsyncConnection

from api.cache import cached
from api.database import get_db
from src.repository import Mentions

router = APIRouter(tags=["news"])


async def get_mentions(conn: AsyncConnection[dict[str, Any]] = Depends(get_db)) -> Mentions:
    return Mentions(conn)


@router.get("/news")
@cached
async def get_latest_news(
    source: str | None = Query(None, max_length=200, description="Filter by source"),
    limit: int = Query(20, ge=1, description="Max results"),
    from_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    repo: Mentions = Depends(get_mentions),
) -> dict[str, Any]:
    rows = await repo.get_recent(source=source, limit=limit, from_date=from_date, to_date=to_date)
    return {"news": rows, "count": len(rows)}
