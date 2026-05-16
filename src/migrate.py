"""Database migration script — creates all tables."""

from src.config import Config
from src.database import Database


def migrate() -> None:
    """Run database migrations."""
    config = Config.from_env()
    db = Database(config.database_url)
    db.initialize()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
