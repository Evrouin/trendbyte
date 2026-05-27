"""Lobste.rs collector — public RSS/JSON, no auth required."""

from __future__ import annotations

import requests

from src.categorization.ner import extract_best_tech_name
from src.categorization.stopwords import is_valid_tech_name
from src.collectors import BaseCollector
from src.infra.logger import Logger
from src.models import Mention
from src.utils import RateLimitError, retry

logger = Logger.get(__name__)

LOBSTERS_URL = "https://lobste.rs/hottest.json"


class LobstersCollector(BaseCollector):
    """Collects hottest stories from Lobste.rs."""

    @property
    def source_name(self) -> str:
        return "lobsters"

    @retry(max_attempts=3, backoff=2.0)
    def collect(self) -> list[Mention]:
        """Fetch hottest stories."""
        response = requests.get(LOBSTERS_URL, timeout=10)

        if response.status_code == 429:
            raise RateLimitError("Lobste.rs rate limit")
        response.raise_for_status()

        stories = response.json()[:30]
        mentions: list[Mention] = []

        for story in stories:
            tags = story.get("tags", [])
            valid_tags = [t for t in tags if is_valid_tech_name(t)]
            name = valid_tags[0] if valid_tags else self._extract_tech_name(story.get("title", ""))
            if not name:
                continue
            mentions.append(
                Mention(
                    source=self.source_name,
                    name=name,
                    url=story.get("url") or story.get("short_id_url", ""),
                    description=story.get("title", ""),
                    stars=story.get("score", 0),
                    score=float(story.get("score", 0)),
                )
            )

        logger.info("Collected mentions", extra={"source": "lobsters", "count": len(mentions)})
        return mentions

    def _extract_tech_name(self, title: str) -> str:
        """Extract tech name using NER."""
        return extract_best_tech_name(title)
