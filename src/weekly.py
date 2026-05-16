"""Weekly summary — aggregates and posts a thread with chart."""

from __future__ import annotations

from datetime import datetime

from src.bot import TwitterBot
from src.gateway import DatabaseGateway
from src.logger import Logger
from src.rendering import ImageRenderer

logger = Logger.get(__name__)


class WeeklySummary:
    """Generates and posts weekly trend summary threads."""

    def __init__(self, db: DatabaseGateway, bot: TwitterBot, renderer: ImageRenderer) -> None:
        self._db = db
        self._bot = bot
        self._renderer = renderer

    def post_weekly_thread(self) -> None:
        """Post a weekly summary thread with chart image."""
        trends = self._db.get_weekly_trends(limit=5)
        if not trends:
            logger.warning("No weekly trends to post")
            return

        # Calculate bar heights relative to max
        max_mentions = max(t["mentions"] for t in trends)
        chart_data = [
            {
                "name": t["name"],
                "mentions": t["mentions"],
                "height": int((t["mentions"] / max_mentions) * 100),
            }
            for t in trends
        ]

        week = datetime.utcnow().strftime("%B %d, %Y")
        image_path = self._renderer.render_weekly_comparison(chart_data, week)

        # Post thread: first tweet with image, then details
        tweets = self._build_thread(trends, week)
        self._bot.post_thread(tweets, image_path)
        logger.info("Weekly thread posted")

    def _build_thread(self, trends: list[dict], week: str) -> list[str]:
        """Build tweet thread text."""
        thread = [f"⚡ TrendByte Weekly Report — {week}\n\nTop 5 technologies this week:\n"]
        for i, t in enumerate(trends, 1):
            thread[0] += f"\n{i}. {t['name']} ({t['mentions']} mentions)"

        thread.append(
            "Key insights:\n\n"
            f"🔥 Hottest: {trends[0]['name']}\n"
            f"📈 Most sources: {trends[0]['name']}\n\n"
            "#TrendByte #WeeklyReport #TechTrends"
        )
        return thread
