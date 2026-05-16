"""Twitter bot for posting trend updates."""

from __future__ import annotations

import logging

import tweepy

from src.models import Post, Trend
from src.rendering.image_renderer import ImageRenderer

logger = logging.getLogger(__name__)


class TwitterBot:
    """Posts trend updates to Twitter with generated images."""

    def __init__(self, config: dict[str, str], renderer: ImageRenderer) -> None:
        auth = tweepy.OAuth1UserHandler(
            config["api_key"],
            config["api_secret"],
            config["access_token"],
            config["access_secret"],
        )
        self._api = tweepy.API(auth)
        self._client = tweepy.Client(
            bearer_token=config["bearer_token"],
            consumer_key=config["api_key"],
            consumer_secret=config["api_secret"],
            access_token=config["access_token"],
            access_token_secret=config["access_secret"],
        )
        self._renderer = renderer

    def post_daily_trends(self, trends: list[Trend], date: str) -> Post | None:
        """Post top 3 trends with a generated image."""
        if not trends:
            logger.warning("No trends to post")
            return None

        top_3 = trends[:3]
        image_path = self._renderer.render_trending_card(
            trends=[
                {
                    "name": t.name,
                    "stars": f"{t.mentions}",
                    "forks": "—",
                    "growth": t.growth_pct,
                }
                for t in top_3
            ],
            date=date,
        )

        tweet_text = self._format_tweet(top_3)
        media = self._api.media_upload(image_path)
        response = self._client.create_tweet(text=tweet_text, media_ids=[media.media_id])

        tweet_id = str(response.data["id"])
        logger.info("Posted tweet", extra={"tweet_id": tweet_id})

        return Post(
            trend_name=top_3[0].name,
            tweet_id=tweet_id,
            tweet_text=tweet_text,
            image_path=image_path,
        )

    def _format_tweet(self, trends: list[Trend]) -> str:
        """Generate tweet text from trend data."""
        lines = ["⚡ Today's Trending Tech\n"]
        for i, t in enumerate(trends, 1):
            lines.append(f"{i}. {t.name} — ↑{t.growth_pct}% | {t.mentions} mentions")
        lines.append("\n#TrendByte #TechTrends")
        return "\n".join(lines)
