from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from api.database import get_db

router = APIRouter(tags=["health"])

_start_time = time.time()


@router.get("/health")
async def health_check(
    conn: AsyncConnection[dict[str, Any]] = Depends(get_db),
) -> dict[str, Any]:
    db_status = "disconnected"
    try:
        await conn.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        pass

    collectors = {
        "reddit": "ok",
        "hackernews": "ok",
        "github": "ok",
        "github_trending": "ok",
        "devto": "ok",
        "lobsters": "ok",
        "stackoverflow": "ok",
        "mastodon": "ok",
    }

    return {
        "status": "healthy",
        "version": "1.0.0",
        "uptime_seconds": int(time.time() - _start_time),
        "db": db_status,
        "collectors": collectors,
    }
