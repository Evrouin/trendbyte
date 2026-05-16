"""Database migration script — creates all tables."""

from src.config import Config
from src.gateway import DatabaseGateway
from src.logger import Logger

Logger.setup()


def migrate() -> None:
    """Run database migrations."""
    config = Config.from_env()
    db = DatabaseGateway(config.database_url)
    db.initialize()


if __name__ == "__main__":
    migrate()
