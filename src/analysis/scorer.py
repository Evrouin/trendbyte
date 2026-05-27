from __future__ import annotations

import math
from datetime import UTC, datetime

from src.analysis.sentiment import average_sentiment
from src.categorization.display_names import to_display_name
from src.categorization.normalizer import normalize
from src.models import Mention, Trend

STAR_NORMALIZERS: dict[str, float] = {
    "reddit": 0.02,
    "hackernews": 0.33,
    "github": 0.1,
    "lobsters": 0.5,
    "devto": 0.2,
    "stackoverflow": 0.25,
    "mastodon": 1.0,
}

HALF_LIFE_DAYS = 7.0


class TrendScorer:
    def score(self, mentions: list[Mention]) -> list[Trend]:
        grouped: dict[str, list[Mention]] = {}
        for m in mentions:
            key = normalize(m.name)
            grouped.setdefault(key, []).append(m)

        now = datetime.now(UTC)
        trends: list[Trend] = []

        for _key, items in grouped.items():
            sources = list({m.source for m in items})
            best = max(items, key=lambda m: m.score)
            sentiment = average_sentiment(items)

            weighted_score = 0.0
            for m in items:
                norm = STAR_NORMALIZERS.get(m.source, 0.1)
                normalized_stars = (m.stars or 0) * norm
                cat = m.collected_at
                if cat.tzinfo is None:
                    cat = cat.replace(tzinfo=UTC)
                age_days = max((now - cat).total_seconds() / 86400, 0.1)
                decay = math.exp(-math.log(2) * age_days / HALF_LIFE_DAYS)
                weighted_score += (1 + normalized_stars) * decay

            source_bonus = 2 ** len(sources)
            frequency_bonus = math.log2(len(items) + 1)
            sentiment_mult = 1 + max(sentiment, 0) * 0.2

            final_score = weighted_score * source_bonus * frequency_bonus * sentiment_mult

            trends.append(
                Trend(
                    name=to_display_name(best.name),
                    mentions=len(items),
                    growth_pct=self._calculate_growth(items, now),
                    score=round(final_score, 1),
                    sources=sources,
                    top_url=best.url,
                )
            )

        trends.sort(key=lambda t: t.score, reverse=True)
        return trends

    def _calculate_growth(self, mentions: list[Mention], now: datetime) -> float:
        if len(mentions) < 2:
            return 0.0
        sorted_m = sorted(
            mentions,
            key=lambda m: m.collected_at.replace(tzinfo=UTC)
            if m.collected_at.tzinfo is None
            else m.collected_at,
        )
        mid = len(sorted_m) // 2
        recent = sorted_m[mid:]
        older = sorted_m[:mid]
        r0 = recent[0].collected_at
        o0 = older[0].collected_at
        if r0.tzinfo is None:
            r0 = r0.replace(tzinfo=UTC)
        if o0.tzinfo is None:
            o0 = o0.replace(tzinfo=UTC)
        recent_days = max((now - r0).total_seconds() / 86400, 1)
        older_days = max((r0 - o0).total_seconds() / 86400, 1)
        recent_velocity = len(recent) / recent_days
        older_velocity = len(older) / older_days
        if older_velocity == 0:
            return 100.0
        growth = ((recent_velocity - older_velocity) / older_velocity) * 100
        return round(max(-999.0, min(999.0, growth)), 1)
