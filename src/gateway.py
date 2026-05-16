"""Database gateway — single entry point for all DB operations."""

from __future__ import annotations

from datetime import datetime

import psycopg
from psycopg.rows import dict_row

from src.logger import Logger
from src.models import Mention, Post, Trend

logger = Logger.get(__name__)


class DatabaseGateway:
    """Encapsulates all database interactions."""

    def __init__(self, database_url: str) -> None:
        self._url = database_url

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self._url, row_factory=dict_row)

    def connection(self) -> psycopg.Connection:
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
                "WHERE posted_at > NOW() - INTERVAL '%s days'",
                (days,),
            ).fetchall()
        return [row["trend_name"] for row in rows]

    def get_weekly_trends(self, limit: int = 5) -> list[dict]:
        """Get top trends from the past 7 days aggregated by mentions."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT name, SUM(mentions) as mentions, AVG(score) as score "
                "FROM trends WHERE calculated_at > NOW() - INTERVAL '7 days' "
                "GROUP BY name ORDER BY mentions DESC LIMIT %s",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
