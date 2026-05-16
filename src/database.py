"""Database connection and schema management."""

from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

SCHEMA = """
CREATE TABLE IF NOT EXISTS mentions (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    description TEXT DEFAULT '',
    stars INTEGER,
    forks INTEGER,
    score FLOAT DEFAULT 0.0,
    collected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trends (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    mentions INTEGER DEFAULT 0,
    growth_pct FLOAT DEFAULT 0.0,
    score FLOAT DEFAULT 0.0,
    sources TEXT[] DEFAULT '{}',
    top_url TEXT DEFAULT '',
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    trend_name VARCHAR(255) NOT NULL,
    tweet_id VARCHAR(100) UNIQUE NOT NULL,
    tweet_text TEXT NOT NULL,
    image_path TEXT,
    posted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mentions_name ON mentions(name);
CREATE INDEX IF NOT EXISTS idx_mentions_collected_at ON mentions(collected_at);
CREATE INDEX IF NOT EXISTS idx_trends_calculated_at ON trends(calculated_at);
CREATE INDEX IF NOT EXISTS idx_posts_trend_name ON posts(trend_name);
"""


class Database:
    """PostgreSQL database wrapper."""

    def __init__(self, database_url: str) -> None:
        self._url = database_url

    def connect(self) -> psycopg.Connection:
        """Return a new database connection."""
        return psycopg.connect(self._url, row_factory=dict_row)

    def initialize(self) -> None:
        """Create tables if they don't exist."""
        with self.connect() as conn:
            conn.execute(SCHEMA)
            conn.commit()
