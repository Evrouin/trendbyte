"""Trends endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from api.db import get_db

router = APIRouter(tags=["trends"])


@router.get("/trends")
def get_trends(
    category: str | None = Query(None, description="Filter by category"),
    days: int = Query(7, description="Timeframe in days"),
    limit: int = Query(10, description="Max results"),
):
    """Get top trends with optional category and timeframe filters."""
    conn = get_db()
    query = (
        "SELECT name, SUM(mentions) as mentions, AVG(score) as score, "
        "AVG(growth_pct) as growth_pct, array_agg(DISTINCT unnest_sources) as sources "
        "FROM trends, unnest(sources) as unnest_sources "
        "WHERE calculated_at > NOW() - INTERVAL '%s days' "
    )
    params: list = [days]

    if category:
        query += (
            "AND LOWER(name) IN ("
            "SELECT ck.keyword FROM category_keywords ck "
            "JOIN categories c ON c.id = ck.category_id WHERE c.name = %s) "
        )
        params.append(category)

    query += "GROUP BY name ORDER BY score DESC LIMIT %s"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {"trends": [dict(r) for r in rows], "count": len(rows)}


@router.get("/trends/{name}")
def get_trend_detail(name: str):
    """Get a single trend with time-series history."""
    conn = get_db()

    # Current stats
    current = conn.execute(
        "SELECT name, mentions, score, growth_pct, sources, top_url, calculated_at "
        "FROM trends WHERE LOWER(name) = LOWER(%s) "
        "ORDER BY calculated_at DESC LIMIT 1",
        (name,),
    ).fetchone()

    # History
    history = conn.execute(
        "SELECT mentions, score, growth_pct, calculated_at "
        "FROM trends WHERE LOWER(name) = LOWER(%s) "
        "ORDER BY calculated_at ASC",
        (name,),
    ).fetchall()

    conn.close()

    if not current:
        return {"error": "Trend not found"}, 404

    return {
        "trend": dict(current),
        "history": [dict(r) for r in history],
    }
