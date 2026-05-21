"""Tests for new collectors."""

from unittest.mock import MagicMock, patch

from src.collectors.github_trending_collector import GithubTrendingCollector
from src.collectors.mastodon_collector import MastodonCollector
from src.collectors.stackoverflow_collector import StackOverflowCollector


def test_stackoverflow_source_name():
    assert StackOverflowCollector().source_name == "stackoverflow"


def test_mastodon_source_name():
    assert MastodonCollector().source_name == "mastodon"


def test_github_trending_source_name():
    assert GithubTrendingCollector().source_name == "github"


@patch("src.collectors.stackoverflow_collector.requests.get")
def test_stackoverflow_parses_response(mock_get: MagicMock):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "items": [
                {
                    "tags": ["python", "pandas"],
                    "title": "How to merge dataframes",
                    "link": "https://stackoverflow.com/q/123",
                    "score": 5,
                    "view_count": 1000,
                },
                {
                    "tags": ["cooking", "food"],
                    "title": "Best recipe",
                    "link": "https://stackoverflow.com/q/456",
                    "score": 2,
                    "view_count": 500,
                },
            ]
        },
    )
    mentions = StackOverflowCollector().collect()
    assert len(mentions) == 1
    assert mentions[0].name == "Python"
    assert mentions[0].source == "stackoverflow"


@patch("src.collectors.mastodon_collector.requests.get")
def test_mastodon_handles_empty(mock_get: MagicMock):
    mock_get.return_value = MagicMock(status_code=200, json=lambda: [])
    mentions = MastodonCollector().collect()
    assert mentions == []


@patch("src.collectors.github_trending_collector.requests.get")
def test_github_trending_fallback_on_404(mock_get: MagicMock):
    mock_get.return_value = MagicMock(status_code=404, text="<html></html>")
    mentions = GithubTrendingCollector().collect()
    assert isinstance(mentions, list)
