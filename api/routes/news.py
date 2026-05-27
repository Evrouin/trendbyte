from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from psycopg import AsyncConnection

from api.cache import cached
from api.database import get_db
from api.schemas import NewsResponse

router = APIRouter(tags=["news"])


@router.get("/news", response_model=NewsResponse)
@cached
async def get_latest_news(
    source: str | None = Query(None, max_length=200, description="Filter by source"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    from_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    conn: AsyncConnection[dict[str, Any]] = Depends(get_db),
) -> dict[str, Any]:
    query = (
        "SELECT source, name, url, description, stars, collected_at "
        "FROM mentions WHERE url != '' AND description != '' "
    )
    params: list[Any] = []

    if source:
        query += "AND source = %s "
        params.append(source)

    if from_date:
        query += "AND collected_at >= %s "
        params.append(from_date)

    if to_date:
        query += "AND collected_at <= %s::date + 1 "
        params.append(to_date)

    query += "ORDER BY collected_at DESC LIMIT %s"
    params.append(limit)

    rows = await (await conn.execute(query, params)).fetchall()
    return {"news": [dict(r) for r in rows], "count": len(rows)}
