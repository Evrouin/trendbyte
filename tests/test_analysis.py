"""Tests for the trend scoring engine."""

from datetime import datetime

from src.analysis import TrendScorer
from src.models import Mention


def _make_mention(name: str, source: str = "github", stars: int = 100) -> Mention:
    return Mention(
        source=source,
        name=name,
        url=f"https://example.com/{name}",
        description="test",
        stars=stars,
        score=float(stars),
        collected_at=datetime.utcnow(),
    )


def test_score_ranks_by_stars() -> None:
    scorer = TrendScorer()
    mentions = [_make_mention("low", stars=10), _make_mention("high", stars=500)]
    trends = scorer.score(mentions)
    assert trends[0].name == "high"


def test_score_groups_by_name() -> None:
    scorer = TrendScorer()
    mentions = [_make_mention("bun", stars=100), _make_mention("bun", stars=200)]
    trends = scorer.score(mentions)
    assert len(trends) == 1
    assert trends[0].mentions == 2


def test_multi_source_boosts_score() -> None:
    scorer = TrendScorer()
    single = [
        _make_mention("bun", source="github", stars=100),
        _make_mention("bun", source="github", stars=100),
    ]
    multi = [
        _make_mention("bun", source="github", stars=100),
        _make_mention("bun", source="reddit", stars=100),
    ]
    single_score = scorer.score(single)[0].score
    multi_score = scorer.score(multi)[0].score
    assert multi_score > single_score


def test_dedup_normalizes_names() -> None:
    scorer = TrendScorer()
    mentions = [
        _make_mention("Golang", source="github", stars=100),
        _make_mention("golang", source="reddit", stars=100),
        _make_mention("Go", source="hackernews", stars=100),
    ]
    trends = scorer.score(mentions)
    assert len(trends) == 1
    assert trends[0].mentions == 3
