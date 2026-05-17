"""TrendByte entry point — orchestrates the full pipeline."""

from __future__ import annotations

import sys
from datetime import datetime

from src.analysis import TrendScorer
from src.bot import TwitterBot
from src.collectors import BaseCollector
from src.collectors.devto_collector import DevtoCollector
from src.collectors.github_collector import GitHubCollector
from src.collectors.hn_collector import HNCollector
from src.collectors.lobsters_collector import LobstersCollector
from src.collectors.reddit_collector import RedditCollector
from src.config import Config
from src.gateway import DatabaseGateway
from src.logger import Logger
from src.migrate import migrate
from src.models import Mention
from src.rendering import ImageRenderer
from src.report import generate_report

Logger.setup()
logger = Logger.get(__name__)


def collect_all(collectors: list[BaseCollector]) -> list[Mention]:
    """Run all collectors and aggregate mentions."""
    mentions: list[Mention] = []
    for collector in collectors:
        try:
            mentions.extend(collector.collect())
        except Exception as e:
            logger.error("Collector failed: %s — %s", collector.source_name, e)
    return mentions


def run(dry_run: bool = False) -> None:
    """Execute the daily TrendByte pipeline."""
    config = Config.from_env()

    if not dry_run:
        db = DatabaseGateway(config.database_url)
        migrate()

    collectors: list[BaseCollector] = [
        GitHubCollector(config.github_token),
        RedditCollector(config.reddit_client_id, config.reddit_client_secret, config.reddit_user_agent),
        HNCollector(),
        DevtoCollector(),
        LobstersCollector(),
    ]

    scorer = TrendScorer()
    renderer = ImageRenderer()

    logger.info("Starting TrendByte pipeline (dry_run=%s)", dry_run)

    mentions = collect_all(collectors)
    logger.info("Total mentions: %d", len(mentions))

    if not dry_run:
        db.save_mentions(mentions)

    # Score, filter already-posted, and rank
    trends = scorer.score(mentions)
    if not dry_run:
        recent = db.get_recent_posts(days=3)
        trends = [t for t in trends if t.name not in recent]

    if not trends:
        logger.warning("No new trends to post")
        return

    logger.info("Top trend: %s (score: %.1f)", trends[0].name, trends[0].score)

    if dry_run:
        logger.info("--- DRY RUN RESULTS ---")
        for i, t in enumerate(trends[:3], 1):
            logger.info("#%d %s | score=%.1f | growth=%.1f%% | sources=%s", i, t.name, t.score, t.growth_pct, t.sources)
        image = renderer.render_trending_card(
            trends=[{"name": t.name, "stars": str(t.mentions), "forks": "—", "growth": t.growth_pct} for t in trends[:3]],
            date=datetime.utcnow().strftime("%B %d, %Y"),
        )
        logger.info("Image generated: %s", image)
        return

    db.save_trends(trends[:10])

    # Generate image regardless
    today = datetime.utcnow().strftime("%B %d, %Y")
    image = renderer.render_trending_card(
        trends=[{"name": t.name, "stars": str(t.mentions), "forks": "—", "growth": t.growth_pct} for t in trends[:3]],
        date=today,
    )
    logger.info("Image generated: %s", image)

    # Generate local report
    report_path = generate_report(trends, len(mentions), image)
    logger.info("Report: %s", report_path)

    # Post to Twitter if configured
    if not config.twitter_api_key or "--no-post" in sys.argv:
        logger.info("Twitter posting disabled — skipping")
        logger.info("Pipeline complete (collect + analyze only)")
        return

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

    post = bot.post_daily_trends(trends, today)

    if post:
        db.save_post(post)
        logger.info("Pipeline complete — tweet: %s", post.tweet_id)
    else:
        logger.warning("Pipeline complete — no tweet posted")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    run(dry_run=dry)
