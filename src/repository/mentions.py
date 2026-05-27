from __future__ import annotations

from typing import Any

from psycopg import AsyncConnection


class Mentions:
    def __init__(self, conn: AsyncConnection[dict[str, Any]]) -> None:
        self._conn = conn

    async def get_recent(
        self,
        source: str | None = None,
        limit: int = 20,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[dict[str, Any]]:
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

        rows = await (await self._conn.execute(query, params)).fetchall()
        return [dict(r) for r in rows]

    async def save(self, mentions: list[dict[str, Any]]) -> None:
        for m in mentions:
            await self._conn.execute(
                "INSERT INTO mentions (source, name, url, description, stars, forks, score) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    m["source"],
                    m["name"],
                    m["url"],
                    m["description"],
                    m["stars"],
                    m["forks"],
                    m["score"],
                ),
            )

    async def get_sources(self) -> list[str]:
        rows = await (await self._conn.execute("SELECT DISTINCT source FROM mentions")).fetchall()
        return [r["source"] for r in rows]
