"""Auto-suggest new category keywords from uncategorized mentions."""

from __future__ import annotations

from dataclasses import dataclass

from src.categorizer import Categorizer
from src.logger import Logger
from src.models import Mention
from src.normalizer import normalize

logger = Logger.get(__name__)


@dataclass(frozen=True)
class KeywordSuggestion:
    """A suggested keyword to add to a category."""

    keyword: str
    suggested_category: str
    occurrences: int
    confidence: float


class KeywordSuggester:
    """Suggests new keywords based on uncategorized mentions."""

    def __init__(self, categorizer: Categorizer, min_occurrences: int = 3) -> None:
        self._categorizer = categorizer
        self._min_occurrences = min_occurrences

    def suggest(self, mentions: list[Mention]) -> list[KeywordSuggestion]:
        """Find frequently uncategorized mentions and suggest categories."""
        uncategorized: dict[str, int] = {}
        for m in mentions:
            name = normalize(m.name)
            if self._categorizer.categorize(name) == ["other"]:
                uncategorized[name] = uncategorized.get(name, 0) + 1

        frequent = {k: v for k, v in uncategorized.items() if v >= self._min_occurrences}

        suggestions: list[KeywordSuggestion] = []
        for keyword, count in frequent.items():
            category, confidence = self._guess_category(keyword, mentions)
            suggestions.append(
                KeywordSuggestion(
                    keyword=keyword,
                    suggested_category=category,
                    occurrences=count,
                    confidence=confidence,
                )
            )

        suggestions.sort(key=lambda s: s.occurrences, reverse=True)
        return suggestions

    def auto_apply(self, mentions: list[Mention], min_confidence: float = 0.7) -> int:
        """Auto-add high-confidence suggestions to the categorizer."""
        suggestions = self.suggest(mentions)
        applied = 0
        for s in suggestions:
            if s.confidence >= min_confidence:
                self._categorizer.add_keyword(s.suggested_category, s.keyword)
                logger.info(
                    "Auto-added keyword '%s' to '%s' (confidence=%.2f, occurrences=%d)",
                    s.keyword,
                    s.suggested_category,
                    s.confidence,
                    s.occurrences,
                )
                applied += 1
        return applied

    def _guess_category(self, keyword: str, mentions: list[Mention]) -> tuple[str, float]:
        """Guess which category a keyword belongs to based on co-occurrence."""
        co_mentions = [m for m in mentions if normalize(m.name) == keyword]
        if not co_mentions:
            return "other", 0.0

        source_hints: dict[str, str] = {
            "github": "languages",
            "devto": "web",
            "hackernews": "languages",
            "lobsters": "languages",
        }

        category_votes: dict[str, int] = {}
        for m in co_mentions:
            hint = source_hints.get(m.source, "other")
            category_votes[hint] = category_votes.get(hint, 0) + 1

        category_clues: dict[str, list[str]] = {
            "ai": ["model", "neural", "training", "inference", "llm", "ai"],
            "web": ["frontend", "backend", "api", "framework", "ui", "app"],
            "devops": ["deploy", "container", "cloud", "infra", "pipeline"],
            "databases": ["database", "query", "sql", "storage", "cache"],
            "security": ["security", "auth", "encrypt", "vulnerability"],
        }

        for m in co_mentions:
            desc = m.description.lower()
            for cat, clues in category_clues.items():
                if any(clue in desc for clue in clues):
                    category_votes[cat] = category_votes.get(cat, 0) + 2

        if not category_votes:
            return "other", 0.0

        best_cat = max(category_votes, key=lambda k: category_votes[k])
        total_votes = sum(category_votes.values())
        confidence = category_votes[best_cat] / total_votes

        return best_cat, round(confidence, 2)
