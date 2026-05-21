"""ArXiv collector — recent AI/ML/PL papers."""

from __future__ import annotations

import xml.etree.ElementTree as ElementTree

import requests

from src.collectors import BaseCollector
from src.logger import Logger
from src.models import Mention
from src.ner import extract_best_tech_name
from src.utils import RateLimitError, retry

logger = Logger.get(__name__)

ARXIV_URL = "https://arxiv.org/api/query"
CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.PL"]


class ArxivCollector(BaseCollector):
    """Collects recent papers from ArXiv in AI/ML/PL categories."""

    @property
    def source_name(self) -> str:
        return "arxiv"

    @retry(max_attempts=3, backoff=5.0)
    def collect(self) -> list[Mention]:
        """Fetch recent papers and extract tech names from titles."""
        import time

        time.sleep(3)
        query = " OR ".join(f"cat:{cat}" for cat in CATEGORIES)
        response = requests.get(
            ARXIV_URL,
            params={
                "search_query": query,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
                "max_results": "50",
            },
            timeout=30,
        )

        if response.status_code == 429:
            raise RateLimitError("ArXiv rate limit")
        if response.status_code == 503:
            logger.warning("ArXiv temporarily unavailable")
            return []
        response.raise_for_status()

        root = ElementTree.fromstring(response.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)

        mentions: list[Mention] = []
        for entry in entries:
            title_el = entry.find("atom:title", ns)
            link_el = entry.find("atom:id", ns)
            title = (
                title_el.text.strip().replace("\n", " ")
                if title_el is not None and title_el.text
                else ""
            )
            url = link_el.text.strip() if link_el is not None and link_el.text else ""

            name = extract_best_tech_name(title)
            if not name:
                continue

            mentions.append(
                Mention(
                    source=self.source_name,
                    name=name,
                    url=url,
                    description=title,
                    stars=0,
                    score=1.0,
                )
            )

        logger.info(
            "Collected mentions", extra={"source": self.source_name, "count": len(mentions)}
        )
        return mentions
