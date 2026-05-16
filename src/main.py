"""TrendByte entry point — orchestrates the full pipeline."""

from __future__ import annotations

import logging
from datetime import datetime

from src.analysis import TrendScorer
from src.bot import TwitterBot
from src.collectors.github_collector import GitHubCollector
from src.config import Config
from src.database import Database
from src.rendering import ImageRenderer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def run() -> None:
    """Execute the daily TrendByte pipeline."""
    config = Config.from_env()

    # Initialize components
    db = Database(config.database_url)
    db.initialize()

    collector = GitHubCollector(config.github_token)
    scorer = TrendScorer()
    renderer = ImageRenderer()
    bot = TwitterBot(
        config={
            "api_key": config.twitter_api_key,
            "api_secret": config.twitter_api_secret,
            "access_token": config.twitter_access_token,
            "access_secret": config.twitter_access_secret,
            "bearer_token": config.twitter_bearer_token,
        },
        renderer=renderer,
    )

    # Pipeline
    logger.info("Starting TrendByte pipeline")

    mentions = collector.collect()
    logger.info("Collected %d mentions", len(mentions))

    # Store mentions
    with db.connect() as conn:
        for m in mentions:
            conn.execute(
                "INSERT INTO mentions (source, name, url, description, stars, forks, score) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (m.source, m.name, m.url, m.description, m.stars, m.forks, m.score),
            )
        conn.commit()

    # Score and rank
    trends = scorer.score(mentions)
    logger.info("Top trend: %s (score: %.1f)", trends[0].name, trends[0].score)

    # Post to Twitter
    today = datetime.utcnow().strftime("%B %d, %Y")
    post = bot.post_daily_trends(trends, today)

    if post:
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO posts (trend_name, tweet_id, tweet_text, image_path) "
                "VALUES (%s, %s, %s, %s)",
                (post.trend_name, post.tweet_id, post.tweet_text, post.image_path),
            )
            conn.commit()
        logger.info("Pipeline complete — tweet posted: %s", post.tweet_id)
    else:
        logger.warning("Pipeline complete — no tweet posted")


if __name__ == "__main__":
    run()
