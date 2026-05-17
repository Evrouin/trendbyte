"""Tests for influence scoring."""

from datetime import datetime, timedelta

from src.analysis.influence import InfluenceScorer
from src.models import Mention


def test_scores_multi_source_spread() -> None:
    scorer = InfluenceScorer()
    now = datetime.utcnow()
    mentions = [
        Mention(
            source="github",
            name="NewTool",
            url="",
            description="",
            stars=100,
            score=100,
            collected_at=now,
        ),
        Mention(
            source="hackernews",
            name="NewTool",
            url="",
            description="",
            stars=50,
            score=50,
            collected_at=now + timedelta(hours=2),
        ),
        Mention(
            source="devto",
            name="NewTool",
            url="",
            description="",
            stars=30,
            score=30,
            collected_at=now + timedelta(hours=6),
        ),
    ]
    scores = scorer.score(mentions)
    assert len(scores) == 1
    assert scores[0].sources_reached == 3
    assert scores[0].time_to_multi_source_hours == 2.0


def test_ignores_single_source() -> None:
    scorer = InfluenceScorer()
    now = datetime.utcnow()
    mentions = [
        Mention(
            source="github",
            name="Solo",
            url="",
            description="",
            stars=100,
            score=100,
            collected_at=now,
        ),
        Mention(
            source="github",
            name="Solo",
            url="",
            description="",
            stars=200,
            score=200,
            collected_at=now + timedelta(hours=1),
        ),
    ]
    scores = scorer.score(mentions)
    assert len(scores) == 0
