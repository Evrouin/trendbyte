"""Trend lifecycle prediction — classifies trends as rising, peaking, stable, or declining."""

from __future__ import annotations

import numpy as np
import psycopg
from psycopg.rows import dict_row

from src.config import Config


def _linear_slope(values: list[float]) -> float:
    """Compute slope via simple linear regression."""
    n = len(values)
    x = np.arange(n, dtype=float)
    y = np.array(values, dtype=float)
    slope = float(np.polyfit(x, y, 1)[0])
    return slope


def predict_lifecycle(name: str) -> dict[str, str | float]:
    """Predict lifecycle phase for a named trend based on score history."""
    config = Config.from_env()
    conn = psycopg.connect(config.database_url, row_factory=dict_row)

    rows = conn.execute(
        "SELECT score FROM trends WHERE LOWER(name) = LOWER(%s) ORDER BY calculated_at ASC",
        (name,),
    ).fetchall()
    conn.close()

    scores = [float(r["score"]) for r in rows]

    return classify_scores(name, scores)


def classify_scores(name: str, scores: list[float]) -> dict[str, str | float]:
    """Classify lifecycle from a list of scores (useful for testing without DB)."""
    if len(scores) < 2:
        return {"name": name, "phase": "stable", "momentum": 0.0}

    recent = scores[-4:] if len(scores) >= 4 else scores
    slope = _linear_slope(recent)

    # Acceleration: compare slope of last half vs first half of recent window
    acceleration = 0.0
    if len(recent) >= 4:
        mid = len(recent) // 2
        slope_first = _linear_slope(recent[:mid])
        slope_second = _linear_slope(recent[mid:])
        acceleration = slope_second - slope_first

    if slope > 0.1 and acceleration >= -1e-9:
        phase = "rising"
    elif slope > 0 and acceleration < -1e-9 and max(recent) == recent[-1]:
        phase = "peaking"
    elif slope < -0.1:
        phase = "declining"
    else:
        phase = "stable"

    return {"name": name, "phase": phase, "momentum": round(slope, 4)}
