"""Tests for lifecycle prediction."""

from src.analysis.lifecycle import classify_scores


def test_rising_trend() -> None:
    scores = [1.0, 2.0, 3.0, 4.0]
    result = classify_scores("test", scores)
    assert result["phase"] == "rising"
    assert result["momentum"] > 0


def test_declining_trend() -> None:
    scores = [10.0, 8.0, 5.0, 2.0]
    result = classify_scores("test", scores)
    assert result["phase"] == "declining"
    assert result["momentum"] < 0


def test_stable_trend() -> None:
    scores = [5.0, 5.1, 4.9, 5.0]
    result = classify_scores("test", scores)
    assert result["phase"] == "stable"


def test_insufficient_data() -> None:
    result = classify_scores("test", [5.0])
    assert result["phase"] == "stable"
    assert result["momentum"] == 0.0


def test_insufficient_data_two_weeks() -> None:
    result = classify_scores("test", [5.0, 6.0])
    assert result["phase"] == "stable"
    assert result["momentum"] == 0.0
