from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from psycopg import AsyncConnection

from api.cache import cached
from api.database import get_db
from src.repository import Predictions

router = APIRouter(tags=["predictions"])


def get_predictions_repo(conn: AsyncConnection[dict[str, Any]] = Depends(get_db)) -> Predictions:
    return Predictions(conn)


@router.get("/predictions")
@cached
async def get_predictions(
    min_confidence: float = Query(0.4, description="Minimum confidence threshold"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    repo: Predictions = Depends(get_predictions_repo),
) -> dict[str, Any]:
    all_preds = await repo.get_all(limit=limit)
    filtered = [p for p in all_preds if p["confidence"] >= min_confidence]
    return {"predictions": filtered, "count": len(filtered)}
