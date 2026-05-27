"""Automated data cleanup pipeline for TrendByte."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import psycopg
from psycopg.rows import dict_row

from src.categorization.display_names import to_display_name

logger = logging.getLogger(__name__)


class DataCleaner:
    """Connects to the DB and performs data normalization and deduplication."""

    def __init__(self, database_url: str) -> None:
        self._db_url = database_url

    def run(self) -> dict[str, int]:
        """Execute all cleanup tasks and return a summary dict."""
        conn = psycopg.connect(self._db_url, row_factory=dict_row)
        summary: dict[str, int] = {}

        summary["mentions_normalized"] = self._normalize_mention_names(conn)
        summary["mentions_merged"] = self._merge_duplicate_mentions(conn)
        summary["predictions_normalized"] = self._normalize_prediction_names(conn)
        summary["predictions_deduped"] = self._deduplicate_predictions(conn)
        summary["predictions_stale_removed"] = self._remove_stale_predictions(conn)
        summary["trends_sources_cleaned"] = self._clean_trends_sources(conn)
        summary["keywords_added"] = self._recategorize_other(conn)

        conn.close()
        logger.info("Cleanup complete: %s", summary)
        return summary

    def _normalize_mention_names(self, conn: psycopg.Connection[Any]) -> int:
        rows = conn.execute("SELECT DISTINCT name FROM mentions").fetchall()
        count = 0
        for row in rows:
            name = row["name"]
            display = to_display_name(name)
            if display != name:
                conn.execute("UPDATE mentions SET name = %s WHERE name = %s", (display, name))
                count += 1
        conn.commit()
        logger.info("Normalized %d mention names", count)
        return count

    def _merge_duplicate_mentions(self, conn: psycopg.Connection[Any]) -> int:
        # Keep the row with the canonical display name for each duplicate URL
        result = conn.execute(
            "DELETE FROM mentions WHERE ctid NOT IN ("
            "  SELECT DISTINCT ON (url) ctid FROM mentions ORDER BY url, name"
            ")"
        )
        count = result.rowcount or 0
        conn.commit()
        logger.info("Merged %d duplicate mentions", count)
        return count

    def _normalize_prediction_names(self, conn: psycopg.Connection[Any]) -> int:
        rows = conn.execute("SELECT DISTINCT name FROM predictions").fetchall()
        count = 0
        for row in rows:
            name = row["name"]
            display = to_display_name(name)
            if display != name:
                conn.execute("UPDATE predictions SET name = %s WHERE name = %s", (display, name))
                count += 1
        conn.commit()
        logger.info("Normalized %d prediction names", count)
        return count

    def _deduplicate_predictions(self, conn: psycopg.Connection[Any]) -> int:
        result = conn.execute(
            "DELETE FROM predictions WHERE ctid NOT IN ("
            "  SELECT DISTINCT ON (name) ctid FROM predictions"
            "  ORDER BY name, predicted_at DESC"
            ")"
        )
        count = result.rowcount or 0
        conn.commit()
        logger.info("Deduped %d predictions", count)
        return count

    def _remove_stale_predictions(self, conn: psycopg.Connection[Any]) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=30)
        result = conn.execute("DELETE FROM predictions WHERE predicted_at < %s", (cutoff,))
        count = result.rowcount or 0
        conn.commit()
        logger.info("Removed %d stale predictions", count)
        return count

    def _clean_trends_sources(self, conn: psycopg.Connection[Any]) -> int:
        valid = conn.execute("SELECT DISTINCT source FROM mentions").fetchall()
        valid_sources = {r["source"] for r in valid}

        rows = conn.execute("SELECT ctid, sources FROM trends WHERE sources IS NOT NULL").fetchall()
        count = 0
        for row in rows:
            sources = row["sources"]
            cleaned = [s for s in sources if s in valid_sources]
            if cleaned != sources:
                conn.execute(
                    "UPDATE trends SET sources = %s WHERE ctid = %s",
                    (cleaned, row["ctid"]),
                )
                count += 1
        conn.commit()
        logger.info("Cleaned sources in %d trends", count)
        return count

    def _recategorize_other(self, conn: psycopg.Connection[Any]) -> int:
        from src.categorization.categorizer import Categorizer

        categorizer = Categorizer(conn)
        names = conn.execute("SELECT DISTINCT name FROM mentions").fetchall()
        count = 0

        try:
            from src.analysis.classifier import predict_proba
        except Exception:
            logger.warning("Classifier unavailable, skipping recategorization")
            return 0

        for row in names:
            name = row["name"]
            cats = categorizer.categorize(name)
            if cats != ["other"]:
                continue
            # Get a description for this tech
            desc_row = conn.execute(
                "SELECT description FROM mentions WHERE name = %s "
                "AND description IS NOT NULL AND description != '' LIMIT 1",
                (name,),
            ).fetchone()
            if not desc_row:
                continue
            proba = predict_proba(desc_row["description"])
            best_cat = max(proba, key=proba.get)  # type: ignore[arg-type]
            if best_cat != "other" and proba[best_cat] > 0.4:
                categorizer.add_keyword(best_cat, name.lower())
                count += 1

        logger.info("Re-categorized %d techs from 'other'", count)
        return count


if __name__ == "__main__":
    from dotenv import load_dotenv

    from src.infra.config import Config

    load_dotenv()
    config = Config.from_env()
    cleaner = DataCleaner(config.database_url)
    result = cleaner.run()
    print(result)
