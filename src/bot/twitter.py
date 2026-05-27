from __future__ import annotations

import tweepy

from src.infra.logger import Logger
from src.models import Post, Trend
from src.rendering import ImageRenderer

logger = Logger.get(__name__)


class TwitterBot:
    def __init__(self, config: dict[str, str], renderer: ImageRenderer) -> None:
        auth = tweepy.OAuth1UserHandler(
            config["api_key"],
            config["api_secret"],
            config["access_token"],
            config["access_secret"],
        )
        self._api = tweepy.API(auth)
        self._client = tweepy.Client(
            bearer_token=config["bearer_token"],
            consumer_key=config["api_key"],
            consumer_secret=config["api_secret"],
            access_token=config["access_token"],
            access_token_secret=config["access_secret"],
        )
        self._renderer = renderer

    def post_daily_trends(self, trends: list[Trend], date: str) -> Post | None:
        if not trends:
            logger.warning("No trends to post")
            return None

        top_3 = trends[:3]
        image_path = self._renderer.render_trending_card(
            trends=[
                {
                    "name": t.name,
                    "stars": f"{t.mentions}",
                    "forks": "—",
                    "growth": t.growth_pct,
                }
                for t in top_3
            ],
            date=date,
        )

        tweet_text = self._format_tweet(top_3)
        media = self._api.media_upload(image_path)
        response = self._client.create_tweet(text=tweet_text, media_ids=[media.media_id])

        tweet_id = str(response.data["id"])
        logger.info("Posted tweet", extra={"tweet_id": tweet_id})

        return Post(
            trend_name=top_3[0].name,
            tweet_id=tweet_id,
            tweet_text=tweet_text,
            image_path=image_path,
        )

    def _format_tweet(self, trends: list[Trend]) -> str:
        lines = ["⚡ Today's Trending Tech\n"]
        for i, t in enumerate(trends, 1):
            lines.append(f"{i}. {t.name} — ↑{t.growth_pct}% | {t.mentions} mentions")
        lines.append("\n#TrendByte #TechTrends")
        return "\n".join(lines)

    def post_thread(self, tweets: list[str], image_path: str | None = None) -> None:
        previous_id = None
        for i, text in enumerate(tweets):
            kwargs: dict[str, object] = {"text": text}
            if previous_id:
                kwargs["in_reply_to_tweet_id"] = previous_id
            if i == 0 and image_path:
                media = self._api.media_upload(image_path)
                kwargs["media_ids"] = [media.media_id]
            response = self._client.create_tweet(**kwargs)
            previous_id = str(response.data["id"])
            logger.info("Thread tweet posted", extra={"tweet_id": previous_id})

    def post_daily(self, content: dict) -> None:
        stat = content.get("stat", {})
        trend = content.get("trend_name", "")
        tag = trend.replace(" ", "").replace("-", "")
        text = (
            f"{content['headline']}\n\n"
            f"{stat.get('value', '')} {stat.get('label', '')}\n\n"
            f"{content.get('takeaway', '')}\n\n"
            f"#TrendByte #{tag}"
        )
        self._client.create_tweet(text=text)
        logger.info("Posted daily content tweet")

    def post_weekly(self, content: dict) -> None:
        tweets = []
        md = content.get("most_discussed", {})
        if md:
            tweets.append(
                f"📊 Most discussed this week: {md.get('name', '')} ({md.get('mentions', 0)} mentions)"
            )
        rt = content.get("rising_tool", {})
        if rt:
            tweets.append(f"🚀 Rising tool: {rt.get('name', '')} (+{rt.get('growth_pct', 0):.0f}%)")
        vibe = content.get("community_vibe", {})
        if vibe:
            sentiment = vibe.get("average_sentiment", 0)
            emoji = "😊" if sentiment > 0 else "😐"
            tweets.append(
                f"{emoji} Community vibe: {sentiment:.2f} avg sentiment | Top positive: {vibe.get('top_positive', '')} | Top negative: {vibe.get('top_negative', '')}"
            )
        faded = content.get("faded", {})
        if faded:
            tweets.append(f"📉 Faded: {faded.get('name', '')} ({faded.get('growth_pct', 0):.0f}%)")
        if tweets:
            self.post_thread(tweets)

    def post_monthly(self, content: dict) -> None:
        tweets = []
        bm = content.get("big_mover", {})
        if bm:
            tweets.append(
                f"🏆 Big mover this month: {bm.get('name', '')} (↑{bm.get('rank_change', 0)} ranks)"
            )
        ur = content.get("under_radar", {})
        if ur:
            tweets.append(
                f"🔍 Under the radar: {ur.get('name', '')} — {ur.get('mentions', 0)} mentions across {ur.get('sources', 0)} sources"
            )
        if tweets:
            self.post_thread(tweets)
