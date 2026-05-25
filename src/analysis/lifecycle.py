"""Trend lifecycle prediction — classifies trends as rising, peaking, stable, or declining."""

from __future__ import annotations

import numpy as np
import psycopg
from psycopg.rows import dict_row

from src.config import Config


def _linear_slope(values: list[float]) -> float:
    """Compute slope via simple linear regression."""
    x = np.arange(len(values), dtype=float)
    y = np.array(values, dtype=float)
    return float(np.polyfit(x, y, 1)[0])


def predict_lifecycle(name: str) -> dict[str, str | float]:
    """Predict lifecycle phase for a named trend based on weekly score averages."""
    config = Config.from_env()
    conn = psycopg.connect(config.database_url, row_factory=dict_row)

    rows = conn.execute(
        "SELECT date_trunc('week', calculated_at) as week, AVG(score) as avg_score "
        "FROM trends WHERE LOWER(name) = LOWER(%s) GROUP BY week ORDER BY week",
        (name,),
    ).fetchall()
    conn.close()

    scores = [float(r["avg_score"]) for r in rows]
    return classify_scores(name, scores)


def classify_scores(name: str, scores: list[float]) -> dict[str, str | float]:
    """Classify lifecycle from a list of weekly average scores."""
    if len(scores) < 3:
        return {"name": name, "phase": "stable", "momentum": 0.0}

    recent = scores[-4:]
    slope = _linear_slope(recent)
    mean = float(np.mean(recent))
    threshold = 0.05 * mean if mean else 0.0

    # Acceleration: slope of second half minus slope of first half
    acceleration = 0.0
    if len(recent) >= 4:
        mid = len(recent) // 2
        acceleration = _linear_slope(recent[mid:]) - _linear_slope(recent[:mid])

    overall_mean = float(np.mean(scores))

    if slope > threshold:
        phase = "rising"
    elif recent[-1] > overall_mean and acceleration < 0:
        phase = "peaking"
    elif slope < -threshold:
        phase = "declining"
    else:
        phase = "stable"

    return {"name": name, "phase": phase, "momentum": round(slope, 4)}
