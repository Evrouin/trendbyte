"""Twitter bot for posting trend updates."""

from __future__ import annotations

from src.logger import Logger

import tweepy

from src.models import Post, Trend
from src.rendering import ImageRenderer

logger = Logger.get(__name__)


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
        """Post top 3 trends, with image if supported."""
        if not trends:
            logger.warning("No trends to post")
            return None

        top_3 = trends[:3]
        tweet_text = self._format_tweet(top_3)

        # Try posting with image, fall back to text-only
        media_id = None
        try:
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
            media = self._api.media_upload(image_path)
            media_id = media.media_id
        except Exception as e:
            logger.warning("Media upload failed (free tier?), posting text only: %s", e)
            image_path = None

        kwargs: dict = {"text": tweet_text}
        if media_id:
            kwargs["media_ids"] = [media_id]

        response = self._client.create_tweet(**kwargs)
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

    def post_thread(self, tweets: list[str], image_path: str | None = None) -> None:
        """Post a thread of tweets, first one optionally with an image."""
        previous_id = None
        for i, text in enumerate(tweets):
            kwargs: dict = {"text": text}
            if previous_id:
                kwargs["in_reply_to_tweet_id"] = previous_id
            if i == 0 and image_path:
                media = self._api.media_upload(image_path)
                kwargs["media_ids"] = [media.media_id]
            response = self._client.create_tweet(**kwargs)
            previous_id = str(response.data["id"])
            logger.info("Thread tweet posted", extra={"tweet_id": previous_id})
