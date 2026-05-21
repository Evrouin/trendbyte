"""Trends endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from api.db import get_db

router = APIRouter(tags=["trends"])


@router.get("/trends")
def get_trends(
    category: str | None = Query(None, description="Filter by category"),
    days: int = Query(7, description="Timeframe in days"),
    limit: int = Query(10, description="Max results"),
) -> dict[str, Any]:
    """Get top trends with optional category and timeframe filters."""
    conn = get_db()
    query = (
        "SELECT name, SUM(mentions) as mentions, AVG(score) as score, "
        "AVG(growth_pct) as growth_pct, array_agg(DISTINCT unnest_sources) as sources "
        "FROM trends, unnest(sources) as unnest_sources "
        "WHERE calculated_at > NOW() - make_interval(days => %s) "
    )
    params: list[Any] = [days]

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

    trends = []
    for r in rows:
        cat = conn.execute(
            "SELECT c.name FROM categories c "
            "JOIN category_keywords ck ON c.id = ck.category_id "
            "WHERE ck.keyword = LOWER(%s) LIMIT 1",
            (r["name"],),
        ).fetchone()
        trend = dict(r)
        trend["category"] = cat["name"] if cat else None
        trends.append(trend)

    conn.close()
    return {"trends": trends, "count": len(trends)}


@router.get("/trends/by-category")
def get_trends_by_category(
    days: int = Query(7, description="Timeframe in days"),
    limit: int = Query(5, description="Max results per category"),
) -> dict[str, Any]:
    """Get top trends grouped by category."""
    conn = get_db()

    cats = conn.execute("SELECT id, name FROM categories ORDER BY name").fetchall()
    result = []

    for cat in cats:
        rows = conn.execute(
            "SELECT t.name, SUM(t.mentions) as mentions, AVG(t.score) as score "
            "FROM trends t "
            "WHERE LOWER(t.name) IN ("
            "  SELECT ck.keyword FROM category_keywords ck WHERE ck.category_id = %s"
            ") AND t.calculated_at > NOW() - make_interval(days => %s) "
            "GROUP BY t.name ORDER BY score DESC LIMIT %s",
            (cat["id"], days, limit),
        ).fetchall()

        if not rows:
            rows = conn.execute(
                "SELECT t.name, SUM(t.mentions) as mentions, AVG(t.score) as score "
                "FROM trends t "
                "WHERE LOWER(t.name) IN ("
                "  SELECT ck.keyword FROM category_keywords ck WHERE ck.category_id = %s"
                ") GROUP BY t.name ORDER BY score DESC LIMIT 1",
                (cat["id"],),
            ).fetchall()

        result.append(
            {
                "category": cat["name"],
                "trends": [dict(r) for r in rows],
            }
        )

    conn.close()
    return {"categories": result}


@router.get("/trends/{name}")
def get_trend_detail(name: str) -> dict[str, Any]:
    """Get a single trend with time-series history and related posts."""
    conn = get_db()

    current = conn.execute(
        "SELECT name, mentions, score, growth_pct, sources, top_url, calculated_at "
        "FROM trends WHERE LOWER(name) = LOWER(%s) "
        "ORDER BY calculated_at DESC LIMIT 1",
        (name,),
    ).fetchone()

    history = conn.execute(
        "SELECT mentions, score, growth_pct, calculated_at "
        "FROM trends WHERE LOWER(name) = LOWER(%s) "
        "ORDER BY calculated_at ASC",
        (name,),
    ).fetchall()

    posts = conn.execute(
        "SELECT DISTINCT ON (url) source, url, description, stars, collected_at "
        "FROM mentions WHERE LOWER(name) = LOWER(%s) AND url != '' "
        "ORDER BY url, stars DESC "
        "LIMIT 10",
        (name,),
    ).fetchall()

    related = conn.execute(
        "SELECT t2.name, AVG(t2.score) as score "
        "FROM trends t1 "
        "JOIN trends t2 ON t2.calculated_at = t1.calculated_at AND t2.name != t1.name "
        "WHERE LOWER(t1.name) = LOWER(%s) "
        "GROUP BY t2.name ORDER BY score DESC LIMIT 5",
        (name,),
    ).fetchall()

    conn.close()

    if not current:
        return {"error": "Trend not found"}

    return {
        "trend": dict(current),
        "history": [dict(r) for r in history],
        "posts": [dict(r) for r in posts],
        "related": [dict(r) for r in related],
    }
