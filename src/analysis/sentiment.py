"""Lightweight sentiment analysis — no heavy dependencies."""

from __future__ import annotations

from src.models import Mention

POSITIVE = {
    "amazing", "awesome", "best", "better", "brilliant", "clean", "easy",
    "elegant", "excellent", "fast", "fantastic", "good", "great", "impressive",
    "incredible", "innovative", "love", "modern", "nice", "perfect", "powerful",
    "simple", "solid", "stable", "superb", "useful", "wonderful",
}

NEGATIVE = {
    "awful", "bad", "broken", "buggy", "complex", "confusing", "crash",
    "dead", "deprecated", "difficult", "disappointing", "error", "fail",
    "flawed", "horrible", "insecure", "issue", "lack", "mess", "outdated",
    "painful", "poor", "problem", "slow", "terrible", "ugly", "unstable",
    "vulnerability", "weak", "worst",
}


def analyze_sentiment(mention: Mention) -> float:
    """Return sentiment score (-1.0 to 1.0) based on keyword matching."""
    if not mention.description:
        return 0.0
    words = set(mention.description.lower().split())
    pos = len(words & POSITIVE)
    neg = len(words & NEGATIVE)
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 3)


def average_sentiment(mentions: list[Mention]) -> float:
    """Return average sentiment across mentions."""
    if not mentions:
        return 0.0
    total = sum(analyze_sentiment(m) for m in mentions)
    return round(total / len(mentions), 3)
