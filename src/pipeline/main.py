"""TrendByte entry point — orchestrates the full pipeline."""

from __future__ import annotations

import sys
from datetime import UTC, datetime

from src.analysis import TrendScorer
from src.analysis.rising_stars import RisingStarDetector
from src.bot import TwitterBot
from src.collectors import BaseCollector
from src.collectors.devto_collector import DevtoCollector
from src.collectors.github_collector import GitHubCollector
from src.collectors.github_trending_collector import GithubTrendingCollector
from src.collectors.hn_collector import HNCollector
from src.collectors.lobsters_collector import LobstersCollector
from src.collectors.mastodon_collector import MastodonCollector
from src.collectors.reddit_collector import RedditCollector
from src.collectors.stackoverflow_collector import StackOverflowCollector
from src.gateway import DatabaseGateway
from src.infra.circuit_breaker import CircuitBreaker
from src.infra.config import Config
from src.infra.logger import Logger
from src.infra.migrate import migrate
from src.models import Mention
from src.rendering import ImageRenderer
from src.report import generate_report

Logger.setup()
logger = Logger.get(__name__)


def collect_all(
    collectors: list[BaseCollector], breakers: dict[str, CircuitBreaker]
) -> list[Mention]:
    """Run all collectors and aggregate mentions."""
    mentions: list[Mention] = []
    for collector in collectors:
        result = breakers[collector.source_name].call(collector.collect)
        if result:
            mentions.extend(result)
        else:
            logger.error("Collector skipped (circuit open or failed): %s", collector.source_name)
    return mentions


def _score_and_save(
    mentions: list[Mention], scorer: TrendScorer, db: DatabaseGateway, dry_run: bool
) -> list:
    trends = scorer.score(mentions)
    if not dry_run:
        recent = db.get_recent_posts(days=3)
        trends = [t for t in trends if t.name not in recent]
    return trends


def _dry_run_output(trends: list, renderer: ImageRenderer) -> None:
    logger.info("--- DRY RUN RESULTS ---")
    for i, t in enumerate(trends[:3], 1):
        logger.info(
            "#%d %s | score=%.1f | growth=%.1f%% | sources=%s",
            i,
            t.name,
            t.score,
            t.growth_pct,
            t.sources,
        )
    image = renderer.render_trending_card(
        trends=[
            {"name": t.name, "stars": str(t.mentions), "forks": "—", "growth": t.growth_pct}
            for t in trends[:3]
        ],
        date=datetime.now(UTC).strftime("%B %d, %Y"),
    )
    logger.info("Image generated: %s", image)


def run(dry_run: bool = False) -> None:
    """Execute the daily TrendByte pipeline."""
    config = Config.from_env()

    if not dry_run:
        db = DatabaseGateway(config.database_url)
        migrate()

    collectors: list[BaseCollector] = [
        GitHubCollector(config.github_token),
        GithubTrendingCollector(),
        RedditCollector(
            config.reddit_client_id, config.reddit_client_secret, config.reddit_user_agent
        ),
        HNCollector(),
        DevtoCollector(),
        LobstersCollector(),
        StackOverflowCollector(),
        MastodonCollector(),
    ]

    scorer = TrendScorer()
    renderer = ImageRenderer()

    logger.info("Starting TrendByte pipeline (dry_run=%s)", dry_run)

    breakers = {c.source_name: CircuitBreaker() for c in collectors}
    mentions = collect_all(collectors, breakers)
    logger.info("Total mentions: %d", len(mentions))

    if not dry_run:
        db.save_mentions(mentions)
        _register_new_techs(mentions, config.database_url)

    trends = _score_and_save(mentions, scorer, db if not dry_run else None, dry_run)

    if not trends:
        logger.warning("No new trends to post")
        return

    logger.info("Top trend: %s (score: %.1f)", trends[0].name, trends[0].score)

    if dry_run:
        _dry_run_output(trends, renderer)
        return

    db.save_trends(trends[:10])

    from src.analysis.lifecycle import predict_lifecycle

    for t in trends[:10]:
        lc = predict_lifecycle(t.name)
        logger.info("Lifecycle %s: phase=%s momentum=%.4f", lc["name"], lc["phase"], lc["momentum"])

    today = datetime.now(UTC).strftime("%B %d, %Y")
    image = renderer.render_trending_card(
        trends=[
            {"name": t.name, "stars": str(t.mentions), "forks": "—", "growth": t.growth_pct}
            for t in trends[:3]
        ],
        date=today,
    )
    logger.info("Image generated: %s", image)

    report_path = generate_report(trends, len(mentions), image)
    logger.info("Report: %s", report_path)

    previous = db.get_previous_mentions(days=7)
    detector = RisingStarDetector(min_confidence=0.4)
    rising = detector.detect(mentions, previous)
    if rising:
        db.save_predictions(rising)
        logger.info("Rising stars detected: %d", len(rising))
        for star in rising[:3]:
            logger.info(
                "  ⭐ %s (confidence=%.2f, signals=%s)", star.name, star.confidence, star.signals
            )

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

    try:
        from src.content.generator import ContentGenerator

        content_gen = ContentGenerator(config.database_url)
        daily_content = content_gen.generate_daily()
        logger.info("Daily content generated: %s", daily_content.get("headline"))

        if not dry_run and config.twitter_api_key:
            bot.post_daily(daily_content)
    except Exception as e:
        logger.error("Content generation/posting failed: %s", e)


def _register_new_techs(mentions: list, database_url: str) -> None:
    try:
        import psycopg

        with psycopg.connect(database_url) as conn:
            for m in mentions:
                alias = m.name.lower().strip()
                if len(alias) < 2:
                    continue
                exists = conn.execute(
                    "SELECT 1 FROM tech_aliases WHERE alias = %s", (alias,)
                ).fetchone()
                if exists:
                    continue
                conn.execute(
                    "INSERT INTO tech_names (canonical_name) VALUES (%s) ON CONFLICT DO NOTHING",
                    (m.name,),
                )
                row = conn.execute(
                    "SELECT id FROM tech_names WHERE canonical_name = %s", (m.name,)
                ).fetchone()
                if row:
                    conn.execute(
                        "INSERT INTO tech_aliases (tech_id, alias, source) VALUES (%s, %s, 'discovered') ON CONFLICT DO NOTHING",
                        (row[0], alias),
                    )
            conn.commit()
    except Exception:
        pass


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    run(dry_run=dry)
