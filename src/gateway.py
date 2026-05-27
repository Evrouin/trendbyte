"""Database gateway — single entry point for all DB operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from src.infra.logger import Logger
from src.models import Mention, Post, Trend

logger = Logger.get(__name__)


class DatabaseGateway:
    """Encapsulates all database interactions."""

    def __init__(self, database_url: str) -> None:
        self._url = database_url

    def _connect(self) -> psycopg.Connection[dict[str, Any]]:
        return psycopg.connect(self._url, row_factory=dict_row)  # type: ignore[return-value]

    def connection(self) -> psycopg.Connection[dict[str, Any]]:
        """Return a connection for external use (e.g., categorizer)."""
        return self._connect()

    def save_mentions(self, mentions: list[Mention]) -> int:
        """Insert mentions and return count saved."""
        with self._connect() as conn:
            for m in mentions:
                conn.execute(
                    "INSERT INTO mentions (source, name, url, description, stars, forks, score) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (m.source, m.name, m.url, m.description, m.stars, m.forks, m.score),
                )
            conn.commit()
        logger.info("Saved %d mentions", len(mentions))
        return len(mentions)

    def save_trends(self, trends: list[Trend]) -> None:
        """Insert calculated trends."""
        with self._connect() as conn:
            for t in trends:
                conn.execute(
                    "INSERT INTO trends (name, mentions, growth_pct, score, sources, top_url) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (t.name, t.mentions, t.growth_pct, t.score, t.sources, t.top_url),
                )
            conn.commit()
        logger.info("Saved %d trends", len(trends))

    def save_post(self, post: Post) -> None:
        """Record a published tweet."""
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO posts (trend_name, tweet_id, tweet_text, image_path) "
                "VALUES (%s, %s, %s, %s)",
                (post.trend_name, post.tweet_id, post.tweet_text, post.image_path),
            )
            conn.commit()
        logger.info("Saved post: %s", post.tweet_id)

    def was_posted_today(self, trend_name: str) -> bool:
        """Check if a trend was already posted today."""
        with self._connect() as conn:
            result = conn.execute(
                "SELECT 1 FROM posts WHERE trend_name = %s AND posted_at::date = %s",
                (trend_name, datetime.utcnow().date()),
            ).fetchone()
        return result is not None

    def get_recent_posts(self, days: int = 7) -> list[str]:
        """Get trend names posted in the last N days."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT trend_name FROM posts "
                "WHERE posted_at > NOW() - make_interval(days => %s)",
                (days,),
            ).fetchall()
        return [row["trend_name"] for row in rows]

    def get_weekly_trends(self, limit: int = 5) -> list[dict[str, Any]]:
        """Get top trends from the past 7 days aggregated by mentions."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT name, SUM(mentions) as mentions, AVG(score) as score "
                "FROM trends WHERE calculated_at > NOW() - INTERVAL '7 days' "
                "GROUP BY name ORDER BY mentions DESC LIMIT %s",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_recent_post_ids(self, days: int = 7) -> list[str]:
        """Get tweet IDs from the last N days."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT tweet_id FROM posts WHERE posted_at > NOW() - make_interval(days => %s)",
                (days,),
            ).fetchall()
        return [row["tweet_id"] for row in rows]

    def get_previous_mentions(self, days: int = 7) -> list[Mention]:
        """Get mentions from previous runs for comparison."""
        from src.models import Mention

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT source, name, url, description, stars, forks, score, collected_at "
                "FROM mentions WHERE collected_at < NOW() - INTERVAL '1 day' "
                "AND collected_at > NOW() - make_interval(days => %s)",
                (days,),
            ).fetchall()
        return [
            Mention(
                source=r["source"],
                name=r["name"],
                url=r["url"],
                description=r["description"],
                stars=r["stars"],
                forks=r["forks"],
                score=r["score"],
                collected_at=r["collected_at"],
            )
            for r in rows
        ]

    def save_predictions(self, rising_stars: list[Any]) -> None:
        """Store rising star predictions, skipping duplicates from same day."""
        from src.categorization.display_names import to_display_name

        with self._connect() as conn:
            for star in rising_stars:
                name = to_display_name(star.name)
                conn.execute(
                    "INSERT INTO predictions (name, confidence, signals, url) "
                    "SELECT %s, %s, %s, %s "
                    "WHERE NOT EXISTS ("
                    "  SELECT 1 FROM predictions WHERE name = %s "
                    "  AND predicted_at > NOW() - INTERVAL '1 day'"
                    ")",
                    (name, star.confidence, star.signals, star.url, name),
                )
            conn.commit()
        logger.info("Saved predictions (deduped)", extra={"count": len(rising_stars)})

    def save_analytics(self, metrics: Any) -> None:
        """Store tweet engagement metrics."""
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO analytics (tweet_id, impressions, likes, retweets, replies) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    metrics.tweet_id,
                    metrics.impressions,
                    metrics.likes,
                    metrics.retweets,
                    metrics.replies,
                ),
            )
            conn.commit()
