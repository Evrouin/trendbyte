"""Tests for Twitter bot."""

from unittest.mock import MagicMock, patch

from src.bot import TwitterBot
from src.models import Trend


def _make_bot() -> TwitterBot:
    config = {
        "api_key": "fake",
        "api_secret": "fake",
        "access_token": "fake",
        "access_secret": "fake",
        "bearer_token": "fake",
    }
    renderer = MagicMock()
    renderer.render_trending_card.return_value = "/tmp/test.png"

    with (
        patch("src.bot.twitter.tweepy.OAuth1UserHandler"),
        patch("src.bot.twitter.tweepy.API"),
        patch("src.bot.twitter.tweepy.Client"),
    ):
        bot = TwitterBot(config=config, renderer=renderer)

    return bot


def test_format_tweet_contains_trends() -> None:
    bot = _make_bot()
    trends = [
        Trend(name="Bun", mentions=50, growth_pct=340.0, score=1000, sources=["github"]),
        Trend(name="Ollama", mentions=30, growth_pct=210.0, score=800, sources=["reddit"]),
        Trend(name="Deno", mentions=20, growth_pct=180.0, score=600, sources=["hackernews"]),
    ]
    text = bot._format_tweet(trends)
    assert "Bun" in text
    assert "Ollama" in text
    assert "Deno" in text
    assert "#TrendByte" in text


def test_format_tweet_includes_growth() -> None:
    bot = _make_bot()
    trends = [Trend(name="Rust", mentions=10, growth_pct=99.5, score=500, sources=["github"])]
    text = bot._format_tweet(trends)
    assert "99.5%" in text


def test_post_daily_trends_returns_none_when_empty() -> None:
    bot = _make_bot()
    result = bot.post_daily_trends([], "May 16, 2026")
    assert result is None


def test_post_daily_trends_calls_twitter() -> None:
    bot = _make_bot()
    bot._api = MagicMock()
    bot._client = MagicMock()
    bot._api.media_upload.return_value = MagicMock(media_id=12345)
    bot._client.create_tweet.return_value = MagicMock(data={"id": "999"})

    trends = [Trend(name="Bun", mentions=50, growth_pct=340.0, score=1000, sources=["github"])]
    post = bot.post_daily_trends(trends, "May 16, 2026")

    assert post is not None
    assert post.tweet_id == "999"
    assert post.trend_name == "Bun"
    bot._api.media_upload.assert_called_once()
    bot._client.create_tweet.assert_called_once()
