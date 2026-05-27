"""Influence scoring — measures cross-platform spread velocity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.categorization.normalizer import normalize
from src.infra.logger import Logger
from src.models import Mention

logger = Logger.get(__name__)


@dataclass(frozen=True)
class InfluenceScore:
    """Measures how quickly a technology spreads across sources."""

    name: str
    spread_velocity: float
    first_seen: datetime
    sources_reached: int
    total_sources: int
    time_to_multi_source_hours: float


class InfluenceScorer:
    """Calculates influence scores based on cross-platform spread."""

    def score(self, mentions: list[Mention]) -> list[InfluenceScore]:
        """Calculate influence scores for all technologies."""
        grouped: dict[str, list[Mention]] = {}
        for m in mentions:
            key = normalize(m.name)
            grouped.setdefault(key, []).append(m)

        scores: list[InfluenceScore] = []
        for _, items in grouped.items():
            if len(items) < 2:
                continue

            sorted_items = sorted(items, key=lambda m: m.collected_at)
            first = sorted_items[0]
            sources = list({m.source for m in items})

            if len(sources) < 2:
                continue

            first_source = first.source
            second_source_mention = next(
                (m for m in sorted_items if m.source != first_source), None
            )

            if not second_source_mention:
                continue

            time_diff = (second_source_mention.collected_at - first.collected_at).total_seconds()
            hours_to_spread = max(time_diff / 3600, 0.1)

            total_hours = max(
                (sorted_items[-1].collected_at - first.collected_at).total_seconds() / 3600, 1
            )
            velocity = (len(sources) / total_hours) * 24

            scores.append(
                InfluenceScore(
                    name=first.name,
                    spread_velocity=round(velocity, 2),
                    first_seen=first.collected_at,
                    sources_reached=len(sources),
                    total_sources=4,
                    time_to_multi_source_hours=round(hours_to_spread, 2),
                )
            )

        scores.sort(key=lambda s: s.spread_velocity, reverse=True)
        return scores
