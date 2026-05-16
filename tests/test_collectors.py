"""Tests for collectors."""

from unittest.mock import MagicMock, patch

from src.collectors.github_collector import GitHubCollector
from src.collectors.hn_collector import HNCollector


def test_github_collector_source_name() -> None:
    collector = GitHubCollector(token="fake")
    assert collector.source_name == "github"


def test_hn_collector_parses_response() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "hits": [
            {
                "title": "Rust is amazing for CLI tools",
                "url": "https://example.com",
                "objectID": "123",
                "points": 200,
            }
        ]
    }

    collector = HNCollector()
    with patch("src.collectors.hn_collector.requests.get", return_value=mock_response):
        mentions = collector.collect()

    assert len(mentions) == 1
    assert mentions[0].source == "hackernews"
    assert mentions[0].stars == 200


def test_hn_collector_extracts_tech_name() -> None:
    collector = HNCollector()
    assert collector._extract_tech_name("Rust is great") == "Rust"
    assert collector._extract_tech_name("why golang wins") == "why"
