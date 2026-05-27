from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from psycopg import AsyncConnection

from api.database import get_db

router = APIRouter(tags=["categories"])


@router.get("/categories/predict")
async def predict_category(
    text: str = Query(..., max_length=200, description="Text to classify"),
) -> dict[str, Any]:
    from src.analysis.classifier import predict, predict_proba

    return {"category": predict(text), "probabilities": predict_proba(text)}


@router.get("/categories")
async def get_categories(
    conn: AsyncConnection[dict[str, Any]] = Depends(get_db),
) -> dict[str, Any]:
    cats = await (
        await conn.execute(
            "SELECT c.name, COUNT(ck.id) as keyword_count "
            "FROM categories c LEFT JOIN category_keywords ck ON c.id = ck.category_id "
            "GROUP BY c.name ORDER BY c.name"
        )
    ).fetchall()

    result = []
    for cat in cats:
        top = await (
            await conn.execute(
                "SELECT t.name, t.score FROM trends t "
                "WHERE LOWER(t.name) IN ("
                "  SELECT ck.keyword FROM category_keywords ck "
                "  JOIN categories c ON c.id = ck.category_id WHERE c.name = %s"
                ") AND t.calculated_at > NOW() - INTERVAL '7 days' "
                "ORDER BY t.score DESC LIMIT 3",
                (cat["name"],),
            )
        ).fetchall()
        result.append(
            {
                "name": cat["name"],
                "keyword_count": cat["keyword_count"],
                "top_trends": [dict(t) for t in top],
            }
        )

    return {"categories": result}
