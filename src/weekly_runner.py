"""Weekly summary runner entry point."""

from src.bot import TwitterBot
from src.gateway import DatabaseGateway
from src.infra.config import Config
from src.infra.logger import Logger
from src.infra.migrate import migrate
from src.pipeline.weekly import WeeklySummary
from src.rendering import ImageRenderer

Logger.setup()


def run() -> None:
    config = Config.from_env()
    migrate()

    db = DatabaseGateway(config.database_url)
    renderer = ImageRenderer()
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

    summary = WeeklySummary(db=db, bot=bot, renderer=renderer)
    summary.post_weekly_thread()


if __name__ == "__main__":
    run()
