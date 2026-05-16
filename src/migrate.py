"""Migration runner — executes numbered SQL files in order."""

from __future__ import annotations

from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from src.categorizer import Categorizer, DEFAULT_CATEGORIES
from src.config import Config
from src.logger import Logger

Logger.setup()
logger = Logger.get(__name__)

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def get_applied(conn: psycopg.Connection) -> set[int]:
    """Get set of already-applied migration versions."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version INTEGER PRIMARY KEY, "
        "name VARCHAR(255) NOT NULL, "
        "applied_at TIMESTAMPTZ DEFAULT NOW())"
    )
    conn.commit()
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row[0] for row in rows}


def migrate() -> None:
    """Run all pending migrations in order."""
    config = Config.from_env()
    conn = psycopg.connect(config.database_url)

    applied = get_applied(conn)
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    for f in files:
        version = int(f.name.split("_")[0])
        if version in applied:
            continue

        logger.info("Applying migration: %s", f.name)
        sql = f.read_text()
        conn.execute(sql)
        conn.execute(
            "INSERT INTO schema_migrations (version, name) VALUES (%s, %s)",
            (version, f.name),
        )
        conn.commit()

    # Seed categories if empty
    row = conn.execute("SELECT COUNT(*) as cnt FROM category_keywords").fetchone()
    if row and row[0] == 0:
        logger.info("Seeding default categories")
        cat_conn = psycopg.connect(config.database_url, row_factory=dict_row)
        categorizer = Categorizer(db_conn=cat_conn)
        categorizer.seed_defaults()
        cat_conn.close()

    conn.close()
    logger.info("Migrations complete")


if __name__ == "__main__":
    migrate()
