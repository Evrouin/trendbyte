from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Path, Query
from psycopg import AsyncConnection

from api.cache import cached
from api.database import get_db
from src.repository import Trends

router = APIRouter(tags=["trends"])


async def get_trends_repo(conn: AsyncConnection[dict[str, Any]] = Depends(get_db)) -> Trends:
    return Trends(conn)


@router.get("/correlations")
@cached
async def get_correlations() -> dict[str, Any]:
    from src.analysis.correlation import find_correlations

    pairs = find_correlations()[:20]
    return {"correlations": pairs, "count": len(pairs)}


@router.get("/trends/names")
async def get_trend_names(
    repo: Trends = Depends(get_trends_repo),
) -> dict[str, Any]:
    names = await repo.get_names()
    return {"names": names}


@router.get("/trends")
@cached
async def get_trends(
    category: str | None = Query(None, max_length=200, description="Filter by category"),
    days: int = Query(7, ge=1, le=365, description="Timeframe in days"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    conn: AsyncConnection[dict[str, Any]] = Depends(get_db),
) -> dict[str, Any]:
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

    rows = await (await conn.execute(query, params)).fetchall()

    trends = []
    for r in rows:
        cat = await (
            await conn.execute(
                "SELECT c.name FROM categories c "
                "JOIN category_keywords ck ON c.id = ck.category_id "
                "WHERE ck.keyword = LOWER(%s) LIMIT 1",
                (r["name"],),
            )
        ).fetchone()
        trend = dict(r)
        trend["category"] = cat["name"] if cat else None
        trends.append(trend)

    return {"trends": trends, "count": len(trends)}


@router.get("/trends/by-category")
@cached
async def get_trends_by_category(
    days: int = Query(7, ge=1, le=365, description="Timeframe in days"),
    limit: int = Query(5, ge=1, le=100, description="Max results per category"),
    conn: AsyncConnection[dict[str, Any]] = Depends(get_db),
) -> dict[str, Any]:
    cats = await (await conn.execute("SELECT id, name FROM categories ORDER BY name")).fetchall()
    result = []

    for cat in cats:
        rows = await (
            await conn.execute(
                "SELECT t.name, SUM(t.mentions) as mentions, AVG(t.score) as score "
                "FROM trends t "
                "WHERE LOWER(t.name) IN ("
                "  SELECT ck.keyword FROM category_keywords ck WHERE ck.category_id = %s"
                ") AND t.calculated_at > NOW() - make_interval(days => %s) "
                "GROUP BY t.name ORDER BY score DESC LIMIT %s",
                (cat["id"], days, limit),
            )
        ).fetchall()

        if not rows:
            rows = await (
                await conn.execute(
                    "SELECT t.name, SUM(t.mentions) as mentions, AVG(t.score) as score "
                    "FROM trends t "
                    "WHERE LOWER(t.name) IN ("
                    "  SELECT ck.keyword FROM category_keywords ck WHERE ck.category_id = %s"
                    ") GROUP BY t.name ORDER BY score DESC LIMIT 1",
                    (cat["id"],),
                )
            ).fetchall()

        result.append({"category": cat["name"], "trends": [dict(r) for r in rows]})

    return {"categories": result}


@router.get("/trends/{name}/lifecycle")
async def get_trend_lifecycle(name: str = Path(..., max_length=200)) -> dict[str, Any]:
    from src.analysis.lifecycle import predict_lifecycle

    return predict_lifecycle(name)


@router.get("/trends/{name}")
async def get_trend_detail(
    name: str = Path(..., max_length=200),
    granularity: str = Query("weekly", description="daily, weekly, or monthly"),
    repo: Trends = Depends(get_trends_repo),
    conn: AsyncConnection[dict[str, Any]] = Depends(get_db),
) -> dict[str, Any]:
    if granularity not in ("daily", "weekly", "monthly"):
        granularity = "weekly"

    current = await repo.get_by_name(name)
    resolved_name = current["name"] if current else name

    history = await repo.get_history(resolved_name, granularity)

    posts = await (
        await conn.execute(
            "SELECT * FROM (SELECT DISTINCT ON (url) source, url, description, stars, collected_at "
            "FROM mentions WHERE LOWER(name) = LOWER(%s) AND url != '' "
            "ORDER BY url, stars DESC) sub ORDER BY stars DESC "
            "LIMIT 10",
            (resolved_name,),
        )
    ).fetchall()

    related = await (
        await conn.execute(
            "SELECT t2.name, AVG(t2.score) as score "
            "FROM trends t1 "
            "JOIN trends t2 ON t2.calculated_at = t1.calculated_at AND t2.name != t1.name "
            "JOIN tech_aliases ta ON ta.alias = LOWER(t2.name) "
            "WHERE LOWER(t1.name) = LOWER(%s) "
            "GROUP BY t2.name ORDER BY score DESC LIMIT 5",
            (resolved_name,),
        )
    ).fetchall()

    if not current:
        return {"error": "Trend not found"}

    lifecycle: dict[str, Any] = {}
    try:
        from src.analysis.lifecycle import predict_lifecycle

        lifecycle = predict_lifecycle(name)
    except Exception:
        pass

    from src.categorization.display_names import to_display_name

    related_list = [{"name": to_display_name(r["name"]), "score": r["score"]} for r in related]
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
            if other and other.lower() not in seen:
                related_list.append({"name": to_display_name(other), "score": pair["correlation"]})
                seen.add(other.lower())
    except Exception:
        pass

    return {
        "trend": current,
        "history": history,
        "posts": [dict(r) for r in posts],
        "related": related_list,
        "lifecycle": lifecycle,
    }
