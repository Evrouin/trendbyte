"""Weekly summary runner entry point."""

from src.bot import TwitterBot
from src.config import Config
from src.gateway import DatabaseGateway
from src.logger import Logger
from src.migrate import migrate
from src.rendering import ImageRenderer
from src.weekly import WeeklySummary

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
