"""Dev.to collector — no auth required."""

from __future__ import annotations

import requests

from src.collectors import BaseCollector
from src.logger import Logger
from src.models import Mention
from src.utils import RateLimitError, retry

logger = Logger.get(__name__)

DEVTO_API = "https://dev.to/api/articles"


class DevtoCollector(BaseCollector):
    """Collects trending articles from Dev.to."""

    @property
    def source_name(self) -> str:
        return "devto"

    @retry(max_attempts=3, backoff=2.0)
    def collect(self) -> list[Mention]:
        """Fetch top articles from the past week."""
        response = requests.get(
            DEVTO_API,
            params={"top": 7, "per_page": 30},
            timeout=10,
        )

        if response.status_code == 429:
            raise RateLimitError("Dev.to rate limit")
        response.raise_for_status()

        articles = response.json()
        mentions: list[Mention] = []

        for article in articles:
            mentions.append(
                Mention(
                    source=self.source_name,
                    name=self._extract_tech_name(article),
                    url=article.get("url", ""),
                    description=article.get("title", ""),
                    stars=article.get("positive_reactions_count", 0),
                    score=float(article.get("positive_reactions_count", 0)),
                )
            )

        logger.info("Collected mentions", extra={"source": "devto", "count": len(mentions)})
        return mentions

    def _extract_tech_name(self, article: dict) -> str:
        """Extract tech name from tags or title."""
        tags = article.get("tag_list", [])
        if tags:
            return tags[0]
        title = article.get("title", "")
        words = title.split()
        for word in words:
            cleaned = word.strip(",:;!?()[]\"'")
            if cleaned and cleaned[0].isupper() and len(cleaned) > 2:
                return cleaned
        return words[0] if words else "unknown"
