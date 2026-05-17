"""Rising stars prediction — identifies repos likely to trend soon."""

from __future__ import annotations

from dataclasses import dataclass

from src.models import Mention
from src.normalizer import normalize


@dataclass(frozen=True)
class RisingStar:
    """A technology predicted to trend."""

    name: str
    confidence: float
    signals: list[str]
    url: str


class RisingStarDetector:
    """Detects technologies showing early signs of trending."""

    def __init__(self, min_confidence: float = 0.5) -> None:
        self._min_confidence = min_confidence

    def detect(self, current: list[Mention], previous: list[Mention]) -> list[RisingStar]:
        """Compare current vs previous mentions to find rising stars."""
        prev_counts = self._count_by_name(previous)
        curr_counts = self._count_by_name(current)

        stars: list[RisingStar] = []
        for name, count in curr_counts.items():
            prev_count = prev_counts.get(name, 0)
            signals: list[str] = []
            confidence = 0.0

            if prev_count == 0 and count >= 2:
                signals.append("new_multi_source")
                confidence += 0.4

            if prev_count > 0:
                growth = (count - prev_count) / prev_count
                if growth >= 1.0:
                    signals.append(f"spike_{int(growth * 100)}%")
                    confidence += min(growth * 0.3, 0.4)

            sources = self._sources_for(name, current)
            if len(sources) >= 3:
                signals.append(f"multi_source_{len(sources)}")
                confidence += 0.2

            confidence = min(confidence, 1.0)
            if confidence >= self._min_confidence and signals:
                best = next((m for m in current if normalize(m.name) == name), None)
                stars.append(
                    RisingStar(
                        name=best.name if best else name,
                        confidence=round(confidence, 2),
                        signals=signals,
                        url=best.url if best else "",
                    )
                )

        stars.sort(key=lambda s: s.confidence, reverse=True)
        return stars

    def _count_by_name(self, mentions: list[Mention]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for m in mentions:
            key = normalize(m.name)
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _sources_for(self, name: str, mentions: list[Mention]) -> set[str]:
        return {m.source for m in mentions if normalize(m.name) == name}
