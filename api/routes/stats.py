from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from api.cache import cached
from api.database import get_db
from src.repository import Mentions

router = APIRouter(tags=["stats"])


async def get_mentions_repo(conn: AsyncConnection[dict[str, Any]] = Depends(get_db)) -> Mentions:
    return Mentions(conn)


@router.get("/stats")
@cached
async def get_stats(
    conn: AsyncConnection[dict[str, Any]] = Depends(get_db),
    mentions_repo: Mentions = Depends(get_mentions_repo),
) -> dict[str, Any]:
    mentions = await (await conn.execute("SELECT COUNT(*) as total FROM mentions")).fetchone()
    trends = await (
        await conn.execute("SELECT COUNT(DISTINCT name) as total FROM trends")
    ).fetchone()
    predictions = await (await conn.execute("SELECT COUNT(*) as total FROM predictions")).fetchone()
    sources = await mentions_repo.get_sources()
    latest_run = await (
        await conn.execute("SELECT MAX(collected_at) as last_run FROM mentions")
    ).fetchone()

    return {
        "total_mentions": mentions["total"] if mentions else 0,
        "total_trends": trends["total"] if trends else 0,
        "total_predictions": predictions["total"] if predictions else 0,
        "active_sources": sources,
        "last_run": latest_run["last_run"] if latest_run else None,
    }
