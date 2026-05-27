"""Stack Overflow collector — trending tags and hot questions."""

from __future__ import annotations

import requests

from src.categorization.display_names import to_display_name
from src.categorization.stopwords import is_valid_tech_name
from src.collectors import BaseCollector
from src.infra.logger import Logger
from src.models import Mention
from src.utils import RateLimitError, retry

logger = Logger.get(__name__)

HOT_QUESTIONS_URL = "https://api.stackexchange.com/2.3/questions"


class StackOverflowCollector(BaseCollector):
    """Collects hot questions from Stack Overflow."""

    @property
    def source_name(self) -> str:
        return "stackoverflow"

    @retry(max_attempts=3, backoff=2.0)
    def collect(self) -> list[Mention]:
        """Fetch hot questions and extract tech from tags."""
        response = requests.get(
            HOT_QUESTIONS_URL,
            params={
                "order": "desc",
                "sort": "hot",
                "site": "stackoverflow",
                "pagesize": "50",
                "filter": "!nNPvSNVZJS",
            },
            timeout=10,
        )

        if response.status_code == 429:
            raise RateLimitError("Stack Overflow rate limit")
        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])
        mentions: list[Mention] = []

        for item in items:
            tags = item.get("tags", [])
            for tag in tags:
                if is_valid_tech_name(tag):
                    mentions.append(
                        Mention(
                            source=self.source_name,
                            name=to_display_name(tag),
                            url=item.get("link", ""),
                            description=item.get("title", ""),
                            stars=item.get("score", 0),
                            score=float(item.get("view_count", 0) / 100),
                        )
                    )
                    break

        logger.info(
            "Collected mentions", extra={"source": self.source_name, "count": len(mentions)}
        )
        return mentions
