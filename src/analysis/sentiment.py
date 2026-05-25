"""Sentiment analysis using VADER — optimized for short social media text."""

from __future__ import annotations

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from src.models import Mention

_analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(mention: Mention) -> float:
    """Return sentiment score (-1.0 to 1.0) using VADER compound score."""
    if not mention.description:
        return 0.0
    return float(_analyzer.polarity_scores(mention.description)["compound"])


def average_sentiment(mentions: list[Mention]) -> float:
    """Return average sentiment across mentions."""
    if not mentions:
        return 0.0
    total = sum(analyze_sentiment(m) for m in mentions)
    return round(total / len(mentions), 3)
