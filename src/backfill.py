"""Backfill script — pulls historical data from Jan 1, 2025 to now."""

from __future__ import annotations

from datetime import datetime, timedelta

import requests

from src.config import Config
from src.display_names import to_display_name
from src.gateway import DatabaseGateway
from src.logger import Logger
from src.models import Mention
from src.ner import extract_best_tech_name
from src.stopwords import is_valid_tech_name

Logger.setup()
logger = Logger.get(__name__)

START_DATE = datetime(2025, 1, 1)
END_DATE = datetime.utcnow()


def backfill_hn(db: DatabaseGateway) -> int:
    """Backfill Hacker News stories week by week."""
    count = 0
    current = START_DATE
    while current < END_DATE:
        next_week = current + timedelta(days=7)
        since = int(current.timestamp())
        until = int(next_week.timestamp())

        try:
            resp = requests.get(
                "https://hn.algolia.com/api/v1/search",
                params={
                    "tags": "story",
                    "numericFilters": f"created_at_i>{since},created_at_i<{until},points>50",
                    "hitsPerPage": 50,
                },
                timeout=15,
            )
            if resp.status_code != 200:
                logger.warning("HN API error %d for week %s", resp.status_code, current.date())
                current = next_week
                continue

            hits = resp.json().get("hits", [])
            mentions = []
            for hit in hits:
                name = extract_best_tech_name(hit.get("title", ""))
                if not name:
                    continue
                mentions.append(
                    Mention(
                        source="hackernews",
                        name=to_display_name(name),
                        url=hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}",
                        description=hit.get("title", ""),
                        stars=hit.get("points", 0),
                        score=float(hit.get("points", 0)),
                        collected_at=current,
                    )
                )

            if mentions:
                db.save_mentions(mentions)
                count += len(mentions)

        except Exception as e:
            logger.error("HN backfill error for %s: %s", current.date(), e)

        current = next_week
        logger.info("HN: %s — %d mentions total", current.date(), count)

    return count


def backfill_devto(db: DatabaseGateway) -> int:
    """Backfill Dev.to top articles by month."""
    count = 0
    for days_ago in [365, 330, 300, 270, 240, 210, 180, 150, 120, 90, 60, 30, 7]:
        try:
            resp = requests.get(
                "https://dev.to/api/articles",
                params={"top": days_ago, "per_page": 50},
                timeout=15,
            )
            if resp.status_code != 200:
                continue

            articles = resp.json()
            mentions = []
            collected_at = END_DATE - timedelta(days=days_ago)

            for article in articles:
                tags = article.get("tag_list", [])
                name = ""
                for tag in tags:
                    if is_valid_tech_name(tag):
                        name = tag
                        break
                if not name:
                    name = extract_best_tech_name(article.get("title", ""))
                if not name:
                    continue

                mentions.append(
                    Mention(
                        source="devto",
                        name=to_display_name(name),
                        url=article.get("url", ""),
                        description=article.get("title", ""),
                        stars=article.get("positive_reactions_count", 0),
                        score=float(article.get("positive_reactions_count", 0)),
                        collected_at=collected_at,
                    )
                )

            if mentions:
                db.save_mentions(mentions)
                count += len(mentions)
                logger.info("Dev.to: top %d days — %d mentions", days_ago, len(mentions))

        except Exception as e:
            logger.error("Dev.to backfill error: %s", e)

    return count


def backfill_lobsters(db: DatabaseGateway) -> int:
    """Backfill Lobsters hottest stories (limited to current page)."""
    count = 0
    try:
        resp = requests.get("https://lobste.rs/hottest.json", timeout=15)
        if resp.status_code != 200:
            return 0

        stories = resp.json()[:50]
        mentions = []
        for story in stories:
            tags = story.get("tags", [])
            name = ""
            for tag in tags:
                if is_valid_tech_name(tag):
                    name = tag
                    break
            if not name:
                name = extract_best_tech_name(story.get("title", ""))
            if not name:
                continue

            mentions.append(
                Mention(
                    source="lobsters",
                    name=to_display_name(name),
                    url=story.get("url") or story.get("short_id_url", ""),
                    description=story.get("title", ""),
                    stars=story.get("score", 0),
                    score=float(story.get("score", 0)),
                    collected_at=END_DATE,
                )
            )

        if mentions:
            db.save_mentions(mentions)
            count = len(mentions)
            logger.info("Lobsters: %d mentions", count)

    except Exception as e:
        logger.error("Lobsters backfill error: %s", e)

    return count


def run() -> None:
    """Run the backfill."""
    config = Config.from_env()
    db = DatabaseGateway(config.database_url)

    logger.info("Starting backfill from %s to %s", START_DATE.date(), END_DATE.date())

    hn_count = backfill_hn(db)
    devto_count = backfill_devto(db)
    lobsters_count = backfill_lobsters(db)

    total = hn_count + devto_count + lobsters_count
    logger.info("Backfill complete: %d total mentions (HN=%d, Dev.to=%d, Lobsters=%d)",
                total, hn_count, devto_count, lobsters_count)


if __name__ == "__main__":
    run()
