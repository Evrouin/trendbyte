"""Tests for ML prediction model."""

from src.analysis.predictor import TrendPredictor
from src.models import Mention


def test_predict_multi_source_scores_higher() -> None:
    predictor = TrendPredictor()
    mentions = [
        Mention(source="github", name="Hot", url="", description="", stars=500, score=500),
        Mention(source="hackernews", name="Hot", url="", description="", stars=200, score=200),
        Mention(source="devto", name="Hot", url="", description="", stars=100, score=100),
        Mention(source="github", name="Cold", url="", description="", stars=50, score=50),
    ]
    predictions = predictor.predict(mentions)
    assert predictions[0].name == "Hot"
    assert predictions[0].will_trend_score > predictions[1].will_trend_score


def test_predict_returns_score_between_0_and_1() -> None:
    predictor = TrendPredictor()
    mentions = [
        Mention(source="github", name="Test", url="", description="", stars=100, score=100),
    ]
    predictions = predictor.predict(mentions)
    assert 0.0 <= predictions[0].will_trend_score <= 1.0


def test_extract_features() -> None:
    predictor = TrendPredictor()
    mentions = [
        Mention(source="github", name="Bun", url="", description="", stars=1000, score=1000),
        Mention(source="hackernews", name="Bun", url="", description="", stars=500, score=500),
    ]
    features = predictor.extract_features(mentions)
    assert len(features) == 1
    assert features[0].mention_count == 2
    assert features[0].source_count == 2
    assert features[0].has_github == 1
    assert features[0].has_hackernews == 1
