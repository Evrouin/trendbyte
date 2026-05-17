"""Trend scoring engine."""

from __future__ import annotations

from src.analysis.sentiment import average_sentiment
from src.display_names import to_display_name
from src.models import Mention, Trend
from src.normalizer import normalize


class TrendScorer:
    """Scores and ranks technologies by mention frequency and velocity."""

    def score(self, mentions: list[Mention]) -> list[Trend]:
        """Aggregate mentions by normalized name and return ranked trends."""
        grouped: dict[str, list[Mention]] = {}
        for m in mentions:
            key = normalize(m.name)
            grouped.setdefault(key, []).append(m)

        trends: list[Trend] = []
        for key, items in grouped.items():
            total_stars = sum(m.stars or 0 for m in items)
            sources = list({m.source for m in items})
            best = max(items, key=lambda m: m.score)
            sentiment = average_sentiment(items)

            raw_score = total_stars * len(sources)
            boosted = raw_score * (1 + max(sentiment, 0))

            trends.append(
                Trend(
                    name=to_display_name(best.name),
                    mentions=len(items),
                    growth_pct=self._calculate_growth(items),
                    score=round(boosted, 1),
                    sources=sources,
                    top_url=best.url,
                )
            )

        trends.sort(key=lambda t: t.score, reverse=True)
        return trends

    def _calculate_growth(self, mentions: list[Mention]) -> float:
        """Calculate growth percentage based on mention velocity."""
        if len(mentions) < 2:
            return 0.0
        sorted_mentions = sorted(mentions, key=lambda m: m.collected_at)
        first_score = sorted_mentions[0].score or 1.0
        last_score = sorted_mentions[-1].score or 1.0
        return round(((last_score - first_score) / first_score) * 100, 1)
