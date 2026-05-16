"""Hacker News collector using Algolia API."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import requests

from src.collectors import BaseCollector
from src.models import Mention
from src.utils import RateLimitError, retry

logger = logging.getLogger(__name__)

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"


class HNCollector(BaseCollector):
    """Collects trending stories from Hacker News."""

    @property
    def source_name(self) -> str:
        return "hackernews"

    @retry(max_attempts=3, backoff=2.0)
    def collect(self) -> list[Mention]:
        """Fetch top stories from the past week."""
        since = int((datetime.utcnow() - timedelta(days=7)).timestamp())

        response = requests.get(
            HN_SEARCH_URL,
            params={
                "tags": "story",
                "numericFilters": f"created_at_i>{since},points>50",
                "hitsPerPage": 30,
            },
            timeout=10,
        )

        if response.status_code == 429:
            raise RateLimitError("HN Algolia rate limit")
        response.raise_for_status()

        hits = response.json().get("hits", [])
        mentions: list[Mention] = []

        for hit in hits:
            mentions.append(
                Mention(
                    source=self.source_name,
                    name=self._extract_tech_name(hit.get("title", "")),
                    url=hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}",
                    description=hit.get("title", ""),
                    stars=hit.get("points", 0),
                    score=float(hit.get("points", 0)),
                )
            )

        logger.info("Collected mentions", extra={"source": "hackernews", "count": len(mentions)})
        return mentions

    def _extract_tech_name(self, title: str) -> str:
        """Extract the most likely technology name from a story title."""
        words = title.split()
        for word in words:
            cleaned = word.strip(",:;!?()[]\"'")
            if cleaned and cleaned[0].isupper() and len(cleaned) > 2:
                return cleaned
        return words[0] if words else "unknown"
