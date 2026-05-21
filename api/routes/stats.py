"""Stats endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from api.cache import cached
from api.db import get_db

router = APIRouter(tags=["stats"])


@router.get("/stats")
@cached
def get_stats() -> dict[str, Any]:
    """Get overall system statistics."""
    conn = get_db()

    mentions = conn.execute("SELECT COUNT(*) as total FROM mentions").fetchone()
    trends = conn.execute("SELECT COUNT(DISTINCT name) as total FROM trends").fetchone()
    predictions = conn.execute("SELECT COUNT(*) as total FROM predictions").fetchone()
    sources = conn.execute("SELECT DISTINCT source FROM mentions").fetchall()
    latest_run = conn.execute("SELECT MAX(collected_at) as last_run FROM mentions").fetchone()

    conn.close()
    return {
        "total_mentions": mentions["total"] if mentions else 0,
        "total_trends": trends["total"] if trends else 0,
        "total_predictions": predictions["total"] if predictions else 0,
        "active_sources": [r["source"] for r in sources],
        "last_run": latest_run["last_run"] if latest_run else None,
    }
