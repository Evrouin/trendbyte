"""Latest news endpoint — recent posts from all sources."""

from __future__ import annotations

from fastapi import APIRouter, Query

from api.db import get_db

router = APIRouter(tags=["news"])


@router.get("/news")
def get_latest_news(
    source: str | None = Query(None, description="Filter by source"),
    limit: int = Query(20, description="Max results"),
):
    """Get latest collected posts/articles across all sources."""
    conn = get_db()

    query = (
        "SELECT source, name, url, description, stars, collected_at "
        "FROM mentions WHERE url != '' AND description != '' "
    )
    params: list = []

    if source:
        query += "AND source = %s "
        params.append(source)

    query += "ORDER BY collected_at DESC LIMIT %s"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {"news": [dict(r) for r in rows], "count": len(rows)}
