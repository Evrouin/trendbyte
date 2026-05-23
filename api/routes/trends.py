"""Trends endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Path, Query

from api.cache import cached
from api.db import get_db

router = APIRouter(tags=["trends"])


@router.get("/correlations")
@cached
def get_correlations() -> dict[str, Any]:
    """Get top 20 correlated tech pairs."""
    from src.analysis.correlation import find_correlations

    pairs = find_correlations()[:20]
    return {"correlations": pairs, "count": len(pairs)}


@router.get("/trends")
@cached
def get_trends(
    category: str | None = Query(None, max_length=200, description="Filter by category"),
    days: int = Query(7, ge=1, le=365, description="Timeframe in days"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
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
@cached
def get_trends_by_category(
    days: int = Query(7, ge=1, le=365, description="Timeframe in days"),
    limit: int = Query(5, ge=1, le=100, description="Max results per category"),
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


@router.get("/trends/{name}/lifecycle")
def get_trend_lifecycle(name: str = Path(..., max_length=200)) -> dict[str, Any]:
    """Get lifecycle phase prediction for a trend."""
    from src.analysis.lifecycle import predict_lifecycle

    return predict_lifecycle(name)


@router.get("/trends/{name}")
def get_trend_detail(name: str = Path(..., max_length=200)) -> dict[str, Any]:
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

    # Lifecycle prediction
    lifecycle: dict[str, Any] = {}
    try:
        from src.analysis.lifecycle import predict_lifecycle

        lifecycle = predict_lifecycle(name)
    except Exception:
        pass

    # Merge correlated trends into related
    related_list = [dict(r) for r in related]
    try:
        from src.analysis.correlation import find_correlations

        correlated = find_correlations()
        name_lower = name.lower()
        seen = {r["name"].lower() for r in related_list}
        for pair in correlated:
            other = (
                pair["tech_b"]
                if pair["tech_a"] == name_lower
                else (pair["tech_a"] if pair["tech_b"] == name_lower else None)
            )
            if other and other not in seen:
                related_list.append({"name": other, "score": pair["correlation"]})
                seen.add(other)
    except Exception:
        pass

    return {
        "trend": dict(current),
        "history": [dict(r) for r in history],
        "posts": [dict(r) for r in posts],
        "related": related_list,
        "lifecycle": lifecycle,
    }
