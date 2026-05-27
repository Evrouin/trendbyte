"""Reddit collector using PRAW."""

from __future__ import annotations

import praw
from prawcore.exceptions import ResponseException

from src.categorization.display_names import to_display_name
from src.categorization.ner import extract_best_tech_name
from src.collectors import BaseCollector
from src.infra.logger import Logger
from src.models import Mention
from src.utils import RateLimitError, retry

logger = Logger.get(__name__)

SUBREDDITS = ["programming", "webdev", "machinelearning", "LocalLLaMA", "Database", "devops"]


class RedditCollector(BaseCollector):
    """Collects trending posts from programming subreddits."""

    def __init__(self, client_id: str, client_secret: str, user_agent: str) -> None:
        self._reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

    @property
    def source_name(self) -> str:
        return "reddit"

    @retry(max_attempts=3, backoff=2.0)
    def collect(self) -> list[Mention]:
        """Fetch top posts from the past week across target subreddits."""
        mentions: list[Mention] = []

        for sub_name in SUBREDDITS:
            try:
                subreddit = self._reddit.subreddit(sub_name)
                for post in subreddit.top(time_filter="week", limit=10):
                    name = extract_best_tech_name(post.title)
                    if not name:
                        continue
                    mentions.append(
                        Mention(
                            source=self.source_name,
                            name=to_display_name(name),
                            url=post.url,
                            description=post.title,
                            stars=post.score,
                            score=float(post.score),
                        )
                    )
            except ResponseException as e:
                if e.response.status_code == 429:
                    raise RateLimitError(f"Reddit rate limit: {e}") from e
                raise

        logger.info("Collected mentions", extra={"source": "reddit", "count": len(mentions)})
        return mentions
