from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from psycopg import AsyncConnection

from api.cache import cached
from api.database import get_db
from api.schemas import PredictionResponse

router = APIRouter(tags=["predictions"])


@router.get("/predictions", response_model=PredictionResponse)
@cached
async def get_predictions(
    min_confidence: float = Query(0.4, description="Minimum confidence threshold"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    conn: AsyncConnection[dict[str, Any]] = Depends(get_db),
) -> dict[str, Any]:
    rows = await (
        await conn.execute(
            "SELECT name, confidence, signals, url, predicted_at "
            "FROM predictions WHERE confidence >= %s "
            "ORDER BY predicted_at DESC, confidence DESC LIMIT %s",
            (min_confidence, limit),
        )
    ).fetchall()
    return {"predictions": [dict(r) for r in rows], "count": len(rows)}
