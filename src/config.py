"""Application configuration loaded from environment variables."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    """Immutable application configuration."""

    twitter_api_key: str
    twitter_api_secret: str
    twitter_access_token: str
    twitter_access_secret: str
    twitter_bearer_token: str
    github_token: str
    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str
    database_url: str

    @classmethod
    def from_env(cls) -> Config:
        """Load configuration from environment variables."""
        return cls(
            twitter_api_key=environ["TWITTER_API_KEY"],
            twitter_api_secret=environ["TWITTER_API_SECRET"],
            twitter_access_token=environ["TWITTER_ACCESS_TOKEN"],
            twitter_access_secret=environ["TWITTER_ACCESS_SECRET"],
            twitter_bearer_token=environ["TWITTER_BEARER_TOKEN"],
            github_token=environ["GITHUB_TOKEN"],
            reddit_client_id=environ["REDDIT_CLIENT_ID"],
            reddit_client_secret=environ["REDDIT_CLIENT_SECRET"],
            reddit_user_agent=environ.get("REDDIT_USER_AGENT", "trendbyte:v0.1.0"),
            database_url=environ.get("DATABASE_URL", "postgresql://localhost:5432/trendbyte"),
        )
