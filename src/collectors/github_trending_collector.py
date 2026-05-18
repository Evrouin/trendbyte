"""GitHub Trending collector — scrapes trending repos, no auth required."""

from __future__ import annotations

import requests

from src.collectors import BaseCollector
from src.display_names import to_display_name
from src.logger import Logger
from src.models import Mention
from src.stopwords import is_valid_tech_name
from src.utils import RateLimitError, retry

logger = Logger.get(__name__)

TRENDING_URL = "https://api.gitterapp.com/repositories"


class GithubTrendingCollector(BaseCollector):
    """Collects trending repos from GitHub via unofficial API."""

    @property
    def source_name(self) -> str:
        return "github_trending"

    @retry(max_attempts=3, backoff=2.0)
    def collect(self) -> list[Mention]:
        """Fetch daily trending repos."""
        response = requests.get(
            TRENDING_URL,
            params={"since": "daily", "spoken_language_code": "en"},
            timeout=10,
        )

        if response.status_code == 429:
            raise RateLimitError("GitHub Trending rate limit")
        if response.status_code != 200:
            logger.warning("GitHub Trending returned %d, trying fallback", response.status_code)
            return self._fallback_collect()

        repos = response.json()[:30]
        mentions: list[Mention] = []

        for repo in repos:
            lang = repo.get("language", "")
            if not lang or not is_valid_tech_name(lang):
                continue
            mentions.append(
                Mention(
                    source=self.source_name,
                    name=to_display_name(lang),
                    url=repo.get("url", ""),
                    description=repo.get("description", "") or repo.get("name", ""),
                    stars=repo.get("stars", 0),
                    score=float(repo.get("currentPeriodStars", 0)),
                )
            )

        logger.info(
            "Collected mentions", extra={"source": self.source_name, "count": len(mentions)}
        )
        return mentions

    def _fallback_collect(self) -> list[Mention]:
        """Fallback: scrape GitHub trending page."""
        response = requests.get(
            "https://github.com/trending",
            headers={"Accept": "text/html"},
            timeout=10,
        )
        if response.status_code != 200:
            return []

        mentions: list[Mention] = []
        lines = response.text.split("\n")
        for line in lines:
            if 'itemprop="programmingLanguage"' in line:
                lang = line.strip().replace("<span", "").replace("</span>", "").strip()
                lang = lang.split(">")[-1].strip() if ">" in lang else lang
                if is_valid_tech_name(lang):
                    mentions.append(
                        Mention(
                            source=self.source_name,
                            name=to_display_name(lang),
                            url="https://github.com/trending",
                            description=f"Trending in {lang}",
                            stars=0,
                            score=0.0,
                        )
                    )

        logger.info("Fallback collected %d mentions", len(mentions))
        return mentions
