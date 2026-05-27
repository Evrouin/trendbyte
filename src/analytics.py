"""Engagement analytics tracker."""

from __future__ import annotations

from dataclasses import dataclass

import tweepy

from src.gateway import DatabaseGateway
from src.infra.logger import Logger

logger = Logger.get(__name__)


@dataclass(frozen=True)
class TweetMetrics:
    tweet_id: str
    impressions: int
    likes: int
    retweets: int
    replies: int


class AnalyticsTracker:
    """Fetches and stores tweet engagement metrics."""

    def __init__(self, client: tweepy.Client, db: DatabaseGateway) -> None:
        self._client = client
        self._db = db

    def track_recent(self) -> int:
        """Fetch metrics for recent posts and store them."""
        posts = self._db.get_recent_post_ids(days=7)
        tracked = 0

        for tweet_id in posts:
            metrics = self._fetch_metrics(tweet_id)
            if metrics:
                self._db.save_analytics(metrics)
                tracked += 1

        logger.info("Tracked %d tweets", tracked)
        return tracked

    def _fetch_metrics(self, tweet_id: str) -> TweetMetrics | None:
        """Fetch metrics for a single tweet."""
        try:
            tweet = self._client.get_tweet(
                tweet_id,
                tweet_fields=["public_metrics"],
            )
            if not tweet.data:
                return None
            m = tweet.data.public_metrics
            return TweetMetrics(
                tweet_id=tweet_id,
                impressions=m.get("impression_count", 0),
                likes=m.get("like_count", 0),
                retweets=m.get("retweet_count", 0),
                replies=m.get("reply_count", 0),
            )
        except Exception as e:
            logger.error("Failed to fetch metrics for %s: %s", tweet_id, e)
            return None
