"""Mastodon collector — public tech posts from popular instances."""

from __future__ import annotations

import requests

from src.collectors import BaseCollector
from src.logger import Logger
from src.models import Mention
from src.ner import extract_best_tech_name
from src.utils import RateLimitError, retry

logger = Logger.get(__name__)

INSTANCES = [
    "https://mastodon.social",
    "https://fosstodon.org",
    "https://hachyderm.io",
]

HASHTAGS = ["programming", "python", "rust", "javascript", "ai", "machinelearning", "opensource"]


class MastodonCollector(BaseCollector):
    """Collects trending posts from Mastodon tech instances."""

    @property
    def source_name(self) -> str:
        return "mastodon"

    @retry(max_attempts=3, backoff=2.0)
    def collect(self) -> list[Mention]:
        """Fetch trending posts from tech-focused Mastodon instances."""
        mentions: list[Mention] = []

        for instance in INSTANCES:
            mentions.extend(self._collect_trending(instance))
            if len(mentions) >= 30:
                break

        logger.info(
            "Collected mentions", extra={"source": self.source_name, "count": len(mentions)}
        )
        return mentions[:30]

    def _collect_trending(self, instance: str) -> list[Mention]:
        """Fetch trending statuses from a single instance."""
        try:
            response = requests.get(
                f"{instance}/api/v1/trends/statuses",
                params={"limit": "20"},
                timeout=10,
            )

            if response.status_code == 429:
                raise RateLimitError(f"Mastodon {instance} rate limit")
            if response.status_code != 200:
                return []

            statuses = response.json()
            mentions: list[Mention] = []

            for status in statuses:
                content = status.get("content", "")
                # Strip HTML tags
                text = content.replace("<p>", " ").replace("</p>", " ")
                for tag in ["<br>", "<br/>", "<a", "</a>", "<span", "</span>"]:
                    text = text.split(tag)[0] if tag in text else text

                tags = [t["name"] for t in status.get("tags", [])]
                name = ""
                for tag in tags:
                    extracted = extract_best_tech_name(tag)
                    if extracted:
                        name = extracted
                        break
                if not name:
                    name = extract_best_tech_name(text[:200])
                if not name:
                    continue

                mentions.append(
                    Mention(
                        source=self.source_name,
                        name=name,
                        url=status.get("url", ""),
                        description=text[:200].strip(),
                        stars=status.get("favourites_count", 0),
                        score=float(
                            status.get("favourites_count", 0) + status.get("reblogs_count", 0)
                        ),
                    )
                )

            return mentions

        except Exception as e:
            logger.warning("Mastodon %s error: %s", instance, e)
            return []
