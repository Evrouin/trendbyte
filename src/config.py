"""Application configuration loaded from environment variables."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    """Immutable application configuration."""

    github_token: str
    database_url: str
    twitter_api_key: str = ""
    twitter_api_secret: str = ""
    twitter_access_token: str = ""
    twitter_access_secret: str = ""
    twitter_bearer_token: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "trendbyte:v0.1.0"

    @classmethod
    def from_env(cls) -> Config:
        """Load configuration from environment variables."""
        return cls(
            github_token=environ["GITHUB_TOKEN"],
            database_url=environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/trendbyte"),
            twitter_api_key=environ.get("TWITTER_API_KEY", ""),
            twitter_api_secret=environ.get("TWITTER_API_SECRET", ""),
            twitter_access_token=environ.get("TWITTER_ACCESS_TOKEN", ""),
            twitter_access_secret=environ.get("TWITTER_ACCESS_SECRET", ""),
            twitter_bearer_token=environ.get("TWITTER_BEARER_TOKEN", ""),
            reddit_client_id=environ.get("REDDIT_CLIENT_ID", ""),
            reddit_client_secret=environ.get("REDDIT_CLIENT_SECRET", ""),
            reddit_user_agent=environ.get("REDDIT_USER_AGENT", "trendbyte:v0.1.0"),
        )
