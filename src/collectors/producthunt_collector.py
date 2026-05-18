"""Product Hunt collector — top daily products."""

from __future__ import annotations

import requests

from src.collectors import BaseCollector
from src.logger import Logger
from src.models import Mention
from src.ner import extract_best_tech_name
from src.stopwords import is_valid_tech_name
from src.utils import RateLimitError, retry

logger = Logger.get(__name__)

PH_URL = "https://www.producthunt.com/frontend/graphql"


class ProductHuntCollector(BaseCollector):
    """Collects top products from Product Hunt."""

    @property
    def source_name(self) -> str:
        return "producthunt"

    @retry(max_attempts=3, backoff=2.0)
    def collect(self) -> list[Mention]:
        """Fetch today's top products via public GraphQL."""
        query = """
        {
          posts(order: VOTES, first: 30) {
            edges {
              node {
                name
                tagline
                votesCount
                url
                topics { edges { node { name } } }
              }
            }
          }
        }
        """
        response = requests.post(
            PH_URL,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code == 429:
            raise RateLimitError("Product Hunt rate limit")
        if response.status_code != 200:
            logger.warning("Product Hunt returned %d", response.status_code)
            return []

        data = response.json()
        edges = (data.get("data") or {}).get("posts", {}).get("edges", [])

        mentions: list[Mention] = []
        for edge in edges:
            node = edge.get("node", {})
            topics = [t["node"]["name"] for t in node.get("topics", {}).get("edges", [])]

            name = ""
            for topic in topics:
                if is_valid_tech_name(topic):
                    name = topic
                    break
            if not name:
                name = extract_best_tech_name(node.get("name", "") + " " + node.get("tagline", ""))
            if not name:
                continue

            mentions.append(
                Mention(
                    source=self.source_name,
                    name=name,
                    url=node.get("url", ""),
                    description=node.get("tagline", ""),
                    stars=node.get("votesCount", 0),
                    score=float(node.get("votesCount", 0)),
                )
            )

        logger.info(
            "Collected mentions", extra={"source": self.source_name, "count": len(mentions)}
        )
        return mentions
