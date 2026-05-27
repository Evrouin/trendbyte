"""Dev.to collector — no auth required."""

from __future__ import annotations

from typing import Any

import requests

from src.categorization.ner import extract_best_tech_name
from src.categorization.stopwords import is_valid_tech_name
from src.collectors import BaseCollector
from src.infra.logger import Logger
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
            name = self._extract_tech_name(article)
            if not name:
                continue
            mentions.append(
                Mention(
                    source=self.source_name,
                    name=name,
                    url=article.get("url", ""),
                    description=article.get("title", ""),
                    stars=article.get("positive_reactions_count", 0),
                    score=float(article.get("positive_reactions_count", 0)),
                )
            )

        logger.info("Collected mentions", extra={"source": "devto", "count": len(mentions)})
        return mentions

    def _extract_tech_name(self, article: dict[str, Any]) -> str:
        """Extract tech name from tags or title using NER."""
        tags = article.get("tag_list", [])
        for tag in tags:
            if is_valid_tech_name(tag):
                return str(tag)
        return extract_best_tech_name(article.get("title", ""))
