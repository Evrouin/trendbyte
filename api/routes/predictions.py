"""Predictions endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from api.cache import cached
from api.db import get_db

router = APIRouter(tags=["predictions"])


@router.get("/predictions")
@cached
def get_predictions(
    min_confidence: float = Query(0.4, description="Minimum confidence threshold"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
) -> dict[str, Any]:
    """Get rising star predictions with confidence scores."""
    conn = get_db()
    rows = conn.execute(
        "SELECT name, confidence, signals, url, predicted_at "
        "FROM predictions WHERE confidence >= %s "
        "ORDER BY predicted_at DESC, confidence DESC LIMIT %s",
        (min_confidence, limit),
    ).fetchall()
    conn.close()
    return {"predictions": [dict(r) for r in rows], "count": len(rows)}
