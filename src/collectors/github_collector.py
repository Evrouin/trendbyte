"""GitHub trending repositories collector."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from github import Github

from src.collectors import BaseCollector
from src.models import Mention

logger = logging.getLogger(__name__)


class GitHubCollector(BaseCollector):
    """Collects trending repositories from GitHub."""

    def __init__(self, token: str) -> None:
        self._client = Github(token)

    @property
    def source_name(self) -> str:
        return "github"

    def collect(self) -> list[Mention]:
        """Fetch repositories created in the last 7 days, sorted by stars."""
        since = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        query = f"created:>{since} stars:>50"

        logger.info("Collecting GitHub repos", extra={"query": query})

        repos = self._client.search_repositories(query=query, sort="stars", order="desc")
        mentions: list[Mention] = []

        for repo in repos[:30]:
            mentions.append(
                Mention(
                    source=self.source_name,
                    name=repo.name,
                    url=repo.html_url,
                    description=repo.description or "",
                    stars=repo.stargazers_count,
                    forks=repo.forks_count,
                    score=float(repo.stargazers_count),
                )
            )

        logger.info("Collected mentions", extra={"count": len(mentions)})
        return mentions
