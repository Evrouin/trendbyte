"""Stats endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from api.db import get_db

router = APIRouter(tags=["stats"])


@router.get("/stats")
def get_stats():
    """Get overall system statistics."""
    conn = get_db()

    mentions = conn.execute("SELECT COUNT(*) as total FROM mentions").fetchone()
    trends = conn.execute("SELECT COUNT(DISTINCT name) as total FROM trends").fetchone()
    predictions = conn.execute("SELECT COUNT(*) as total FROM predictions").fetchone()
    sources = conn.execute("SELECT DISTINCT source FROM mentions").fetchall()
    latest_run = conn.execute("SELECT MAX(collected_at) as last_run FROM mentions").fetchone()

    conn.close()
    return {
        "total_mentions": mentions["total"],
        "total_trends": trends["total"],
        "total_predictions": predictions["total"],
        "active_sources": [r["source"] for r in sources],
        "last_run": latest_run["last_run"],
    }
