"""Correlation detection — finds techs that trend together."""

from __future__ import annotations

import numpy as np
import psycopg
from psycopg.rows import dict_row

from src.infra.config import Config


def find_correlations(min_correlation: float = 0.5, min_weeks: int = 4) -> list[dict]:
    """Find correlated tech pairs from weekly mention counts."""
    config = Config.from_env()
    conn = psycopg.connect(config.database_url, row_factory=dict_row)

    rows = conn.execute(
        "SELECT LOWER(name) as name, "
        "DATE_TRUNC('week', collected_at) as week, "
        "COUNT(*) as cnt "
        "FROM mentions "
        "GROUP BY LOWER(name), DATE_TRUNC('week', collected_at) "
        "ORDER BY week"
    ).fetchall()
    conn.close()

    if not rows:
        return []

    # Build matrix: weeks x techs
    weeks_set: list[str] = sorted({str(r["week"]) for r in rows})
    techs: list[str] = sorted({r["name"] for r in rows})
    week_idx = {w: i for i, w in enumerate(weeks_set)}
    tech_idx = {t: i for i, t in enumerate(techs)}

    matrix = np.zeros((len(weeks_set), len(techs)))
    for r in rows:
        matrix[week_idx[str(r["week"])], tech_idx[r["name"]]] = int(r["cnt"])

    results: list[dict] = []
    n_techs = len(techs)

    for i in range(n_techs):
        for j in range(i + 1, n_techs):
            col_i = matrix[:, i]
            col_j = matrix[:, j]
            # Count co-occurring weeks (both non-zero)
            co_mask = (col_i > 0) & (col_j > 0)
            co_occurrences = int(co_mask.sum())
            if co_occurrences < min_weeks:
                continue
            # Pearson correlation on weeks where both appear
            if col_i.std() == 0 or col_j.std() == 0:
                continue
            corr = float(np.corrcoef(col_i, col_j)[0, 1])
            if corr > min_correlation:
                results.append(
                    {
                        "tech_a": techs[i],
                        "tech_b": techs[j],
                        "correlation": round(corr, 4),
                        "co_occurrences": co_occurrences,
                    }
                )

    results.sort(key=lambda x: x["correlation"], reverse=True)
    return results
