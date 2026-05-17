"""Tests for sentiment analysis."""

from src.analysis.sentiment import analyze_sentiment, average_sentiment
from src.models import Mention


def _mention(desc: str) -> Mention:
    return Mention(source="test", name="test", url="", description=desc)


def test_positive_sentiment() -> None:
    m = _mention("This is an amazing and wonderful framework")
    assert analyze_sentiment(m) > 0


def test_negative_sentiment() -> None:
    m = _mention("This is terrible and broken")
    assert analyze_sentiment(m) < 0


def test_neutral_sentiment() -> None:
    m = _mention("Version 2.0 released today")
    assert analyze_sentiment(m) == 0.0


def test_empty_description() -> None:
    m = _mention("")
    assert analyze_sentiment(m) == 0.0


def test_average_sentiment() -> None:
    mentions = [_mention("great tool"), _mention("awful mess")]
    avg = average_sentiment(mentions)
    assert avg == 0.0
