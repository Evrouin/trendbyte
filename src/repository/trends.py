from __future__ import annotations

from typing import Any

from psycopg import AsyncConnection


class Trends:
    def __init__(self, conn: AsyncConnection[dict[str, Any]]) -> None:
        self._conn = conn

    async def get_top(self, days: int = 7, limit: int = 10) -> list[dict[str, Any]]:
        rows = await (
            await self._conn.execute(
                "SELECT name, SUM(mentions) as mentions, AVG(score) as score, "
                "AVG(growth_pct) as growth_pct, array_agg(DISTINCT unnest_sources) as sources "
                "FROM trends, unnest(sources) as unnest_sources "
                "WHERE calculated_at > NOW() - make_interval(days => %s) "
                "GROUP BY name ORDER BY score DESC LIMIT %s",
                (days, limit),
            )
        ).fetchall()
        return [dict(r) for r in rows]

    async def get_by_name(self, name: str) -> dict[str, Any] | None:
        row = await (
            await self._conn.execute(
                "SELECT name, mentions, score, growth_pct, sources, top_url, calculated_at "
                "FROM trends WHERE LOWER(name) = LOWER(%s) "
                "ORDER BY calculated_at DESC LIMIT 1",
                (name,),
            )
        ).fetchone()
        if not row:
            row = await (
                await self._conn.execute(
                    "SELECT name, mentions, score, growth_pct, sources, top_url, calculated_at "
                    "FROM trends WHERE LOWER(REPLACE(REPLACE(REPLACE(REPLACE(name, '#', 'sharp'), '++', 'plusplus'), '.', '-'), ' ', '-')) = LOWER(%s) "
                    "ORDER BY calculated_at DESC LIMIT 1",
                    (name,),
                )
            ).fetchone()
        return dict(row) if row else None

    async def get_history(self, name: str, granularity: str = "weekly") -> list[dict[str, Any]]:
        if granularity == "daily":
            trunc = "day"
        elif granularity == "monthly":
            trunc = "month"
        else:
            trunc = "week"
        rows = await (
            await self._conn.execute(
                f"SELECT date_trunc('{trunc}', calculated_at) as calculated_at, "
                "AVG(score) as score, SUM(mentions) as mentions "
                "FROM trends WHERE LOWER(name) = LOWER(%s) "
                "GROUP BY 1 ORDER BY 1",
                (name,),
            )
        ).fetchall()
        return [dict(r) for r in rows]

    async def get_names(self) -> list[str]:
        rows = await (
            await self._conn.execute("SELECT DISTINCT name FROM trends ORDER BY name")
        ).fetchall()
        return [r["name"] for r in rows]

    async def save(self, trends: list[dict[str, Any]]) -> None:
        for t in trends:
            await self._conn.execute(
                "INSERT INTO trends (name, mentions, growth_pct, score, sources, top_url) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (t["name"], t["mentions"], t["growth_pct"], t["score"], t["sources"], t["top_url"]),
            )
