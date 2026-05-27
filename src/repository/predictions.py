from __future__ import annotations

from typing import Any

from psycopg import AsyncConnection


class Predictions:
    def __init__(self, conn: AsyncConnection[dict[str, Any]]) -> None:
        self._conn = conn

    async def get_all(self, limit: int = 10) -> list[dict[str, Any]]:
        rows = await (
            await self._conn.execute(
                "SELECT name, confidence, signals, url, predicted_at "
                "FROM predictions ORDER BY predicted_at DESC, confidence DESC LIMIT %s",
                (limit,),
            )
        ).fetchall()
        return [dict(r) for r in rows]

    async def save(self, predictions: list[dict[str, Any]]) -> None:
        for p in predictions:
            await self._conn.execute(
                "INSERT INTO predictions (name, confidence, signals, url) "
                "SELECT %s, %s, %s, %s "
                "WHERE NOT EXISTS ("
                "  SELECT 1 FROM predictions WHERE name = %s "
                "  AND predicted_at > NOW() - INTERVAL '1 day'"
                ")",
                (p["name"], p["confidence"], p["signals"], p["url"], p["name"]),
            )

    async def get_labeled(self, min_count: int = 1) -> list[dict[str, Any]]:
        rows = await (
            await self._conn.execute(
                "SELECT name, COUNT(*) as count, AVG(confidence) as avg_confidence "
                "FROM predictions GROUP BY name HAVING COUNT(*) >= %s "
                "ORDER BY avg_confidence DESC",
                (min_count,),
            )
        ).fetchall()
        return [dict(r) for r in rows]
