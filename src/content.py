"""Content generation system for daily, weekly, and monthly reports."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import psycopg
from psycopg.rows import dict_row

from src.analysis.lifecycle import predict_lifecycle
from src.analysis.sentiment import analyze_sentiment, average_sentiment
from src.models import Mention


class ContentGenerator:
    """Generates structured content for API and Twitter publishing."""

    def __init__(self, database_url: str) -> None:
        self._db_url = database_url

    def _connect(self) -> psycopg.Connection[dict[str, Any]]:
        return psycopg.connect(self._db_url, row_factory=dict_row)

    def generate_daily(self) -> dict:
        """Pick top trend from last 24h, generate headline + stat + takeaway."""
        since = datetime.now(UTC) - timedelta(hours=24)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT name, score, mentions, stars, sources "
                "FROM trends WHERE calculated_at >= %s ORDER BY score DESC LIMIT 1",
                (since,),
            ).fetchone()

        if not row:
            return {
                "type": "daily",
                "headline": "No trends today",
                "stat": {},
                "takeaway": "",
                "source_badge": "",
                "trend_name": "",
                "generated_at": datetime.now(UTC).isoformat(),
            }

        name = row["name"]
        stat_value = row.get("stars") or row["mentions"]
        stat_label = "stars" if row.get("stars") else "mentions"

        try:
            lc = predict_lifecycle(name)
            phase = str(lc["phase"])
        except Exception:
            phase = "stable"

        takeaway_map = {
            "rising": f"{name} is gaining momentum — watch this space.",
            "peaking": f"{name} is at peak hype — evaluate now.",
            "declining": f"{name} is cooling off — consider alternatives.",
            "stable": f"{name} holds steady — reliable choice.",
        }
        takeaway = takeaway_map.get(phase, f"{name} is trending.")

        return {
            "type": "daily",
            "headline": f"{name} is today's top trend",
            "stat": {"value": stat_value, "label": stat_label, "delta": f"+{row['score']:.0f}"},
            "takeaway": takeaway,
            "source_badge": ", ".join(row["sources"]) if row["sources"] else "",
            "trend_name": name,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def generate_weekly(self) -> dict:
        """Most discussed, rising tool, community vibe, faded trend."""
        since = datetime.now(UTC) - timedelta(days=7)
        with self._connect() as conn:
            most_discussed = conn.execute(
                "SELECT name, SUM(mentions) as total_mentions "
                "FROM trends WHERE calculated_at >= %s GROUP BY name ORDER BY total_mentions DESC LIMIT 1",
                (since,),
            ).fetchone()

            rising_tool = conn.execute(
                "SELECT name, growth_pct FROM trends WHERE calculated_at >= %s "
                "AND growth_pct > 0 AND growth_pct < 500 "
                "AND mentions >= 3 AND mentions <= 50 "
                "ORDER BY growth_pct DESC LIMIT 1",
                (since,),
            ).fetchone()

            faded = conn.execute(
                "SELECT name, growth_pct FROM trends WHERE calculated_at >= %s "
                "AND growth_pct < 0 ORDER BY growth_pct ASC LIMIT 1",
                (since,),
            ).fetchone()

            mention_rows = conn.execute(
                "SELECT name, description FROM mentions WHERE collected_at >= %s",
                (since,),
            ).fetchall()

        # Community vibe
        mentions_objs = [
            Mention(source="", name=r["name"], url="", description=r.get("description", ""))
            for r in mention_rows
        ]
        avg_sent = average_sentiment(mentions_objs)

        # Per-trend sentiment (require 3+ mentions)
        trend_sentiments: dict[str, list[float]] = {}
        for m in mentions_objs:
            s = analyze_sentiment(m)
            trend_sentiments.setdefault(m.name, []).append(s)

        trend_avgs = {k: sum(v) / len(v) for k, v in trend_sentiments.items() if len(v) >= 3}
        top_positive = max(
            (k for k, v in trend_avgs.items() if v > 0),
            key=lambda k: len(trend_sentiments[k]),
            default="",
        )
        top_negative = min(trend_avgs, key=trend_avgs.get, default="") if trend_avgs else ""  # type: ignore[arg-type]

        # Classify rising tool lifecycle
        rising_phase = "rising"
        if rising_tool:
            try:
                lc = predict_lifecycle(rising_tool["name"])
                rising_phase = str(lc["phase"])
            except Exception:
                pass

        return {
            "type": "weekly",
            "most_discussed": {
                "name": most_discussed["name"],
                "mentions": most_discussed["total_mentions"],
            }
            if most_discussed
            else {},
            "rising_tool": {
                "name": rising_tool["name"],
                "growth_pct": rising_tool["growth_pct"],
                "phase": rising_phase,
            }
            if rising_tool
            else {},
            "community_vibe": {
                "average_sentiment": avg_sent,
                "top_positive": top_positive,
                "top_negative": top_negative,
            },
            "faded": {"name": faded["name"], "growth_pct": faded["growth_pct"]} if faded else {},
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def generate_monthly(self) -> dict:
        """Big mover, sustained hype, flash in pan, under radar, top 10."""
        now = datetime.now(UTC)
        since_30 = now - timedelta(days=30)
        since_60 = now - timedelta(days=60)

        with self._connect() as conn:
            current = conn.execute(
                "SELECT name, AVG(score) as avg_score, SUM(mentions) as total_mentions, "
                "MAX(growth_pct) as max_growth, array_agg(DISTINCT unnest_sources) as sources_list "
                "FROM trends, LATERAL unnest(sources) AS unnest_sources "
                "WHERE calculated_at >= %s GROUP BY name",
                (since_30,),
            ).fetchall()

            previous = conn.execute(
                "SELECT name, AVG(score) as avg_score "
                "FROM trends WHERE calculated_at >= %s AND calculated_at < %s GROUP BY name",
                (since_60, since_30),
            ).fetchall()

            weekly_presence = conn.execute(
                "SELECT name, COUNT(DISTINCT date_trunc('week', calculated_at)) as weeks "
                "FROM trends WHERE calculated_at >= %s GROUP BY name",
                (since_30,),
            ).fetchall()

        prev_map = {r["name"]: r["avg_score"] for r in previous}
        weeks_map = {r["name"]: r["weeks"] for r in weekly_presence}

        # Rank improvement (big mover)
        current_ranked = sorted(current, key=lambda r: r["avg_score"], reverse=True)
        prev_ranked_names = sorted(prev_map.keys(), key=lambda n: prev_map[n], reverse=True)
        prev_rank_map = {n: i for i, n in enumerate(prev_ranked_names)}

        big_mover = None
        best_improvement = 0
        for i, r in enumerate(current_ranked):
            if r["name"] in prev_rank_map:
                improvement = prev_rank_map[r["name"]] - i
                if improvement > best_improvement:
                    best_improvement = improvement
                    big_mover = {"name": r["name"], "rank_change": improvement}

        # Sustained hype: rising/stable + 3+ weeks
        sustained_hype = []
        for r in current_ranked:
            if weeks_map.get(r["name"], 0) >= 3:
                try:
                    lc = predict_lifecycle(r["name"])
                    if lc["phase"] in ("rising", "stable"):
                        sustained_hype.append(
                            {"name": r["name"], "weeks": weeks_map[r["name"]], "phase": lc["phase"]}
                        )
                except Exception:
                    pass

        # Flash in pan: appeared then declining
        flash_in_pan = []
        for r in current_ranked:
            if r["name"] not in prev_map:
                try:
                    lc = predict_lifecycle(r["name"])
                    if lc["phase"] == "declining":
                        flash_in_pan.append({"name": r["name"]})
                except Exception:
                    pass

        # Under radar: mentions < 15, sources >= 3, sentiment > 0.3
        under_radar = None
        with self._connect() as conn:
            for r in current_ranked:
                if r["total_mentions"] < 15 and len(r.get("sources_list") or []) >= 3:
                    mention_rows = conn.execute(
                        "SELECT description FROM mentions WHERE LOWER(name) = LOWER(%s) AND collected_at >= %s",
                        (r["name"], since_30),
                    ).fetchall()
                    objs = [
                        Mention(
                            source="",
                            name=r["name"],
                            url="",
                            description=row.get("description", ""),
                        )
                        for row in mention_rows
                    ]
                    if average_sentiment(objs) > 0.3:
                        under_radar = {
                            "name": r["name"],
                            "mentions": r["total_mentions"],
                            "sources": len(r["sources_list"]),
                        }
                        break

        top_10 = [
            {"name": r["name"], "score": round(float(r["avg_score"]), 2)}
            for r in current_ranked[:10]
        ]

        return {
            "type": "monthly",
            "big_mover": big_mover or {},
            "sustained_hype": sustained_hype[:5],
            "flash_in_pan": flash_in_pan[:5],
            "under_radar": under_radar or {},
            "top_10": top_10,
            "generated_at": now.isoformat(),
        }
