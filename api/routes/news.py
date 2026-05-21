"""Latest news endpoint — recent posts from all sources."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from api.cache import cached
from api.db import get_db

router = APIRouter(tags=["news"])


@router.get("/news")
@cached
def get_latest_news(
    source: str | None = Query(None, description="Filter by source"),
    limit: int = Query(20, description="Max results"),
    from_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
) -> dict[str, Any]:
    """Get latest collected posts/articles across all sources."""
    conn = get_db()

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

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {"news": [dict(r) for r in rows], "count": len(rows)}
