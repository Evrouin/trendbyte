"""Database dependency for API routes."""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

from src.config import Config

config = Config.from_env()


def get_db() -> psycopg.Connection[dict[str, Any]]:
    """Return a database connection."""
    return psycopg.connect(config.database_url, row_factory=dict_row)  # type: ignore[return-value]
