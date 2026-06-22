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
        conn = psycopg.connect(self._db_url, row_factory=dict_row)
        summary: dict[str, int] = {}

        summary["mentions_normalized"] = self._normalize_mention_names(conn)
        summary["mentions_merged"] = self._merge_duplicate_mentions(conn)
        summary["predictions_normalized"] = self._normalize_prediction_names(conn)
        summary["predictions_deduped"] = self._deduplicate_predictions(conn)
        summary["predictions_stale_removed"] = self._remove_stale_predictions(conn)
        summary["trends_sources_cleaned"] = self._clean_trends_sources(conn)
        summary["keywords_added"] = self._recategorize_other(conn)
        summary["techs_categorized"] = self._categorize_new_techs(conn)
        summary["techs_flagged_ambiguous"] = self._flag_ambiguous_techs(conn)
        summary["mentions_no_context_removed"] = self._remove_ambiguous_without_context(conn)
        summary["invalid_predictions_removed"] = self._remove_invalid_tech_predictions(conn)

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
        result = conn.execute(
            "DELETE FROM mentions WHERE ctid NOT IN ("
            "  SELECT DISTINCT ON (name, url) ctid FROM mentions ORDER BY name, url, collected_at DESC"
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

    def _categorize_new_techs(self, conn: psycopg.Connection[Any]) -> int:
        try:
            from src.analysis.classifier import predict_proba
        except Exception:
            return 0

        rows = conn.execute(
            "SELECT id, canonical_name FROM tech_names WHERE category_id IS NULL"
        ).fetchall()
        count = 0
        for row in rows:
            proba = predict_proba(row["canonical_name"])
            if not proba:
                continue
            best = max(proba, key=proba.get)
            if proba[best] < 0.4:
                continue
            cat = conn.execute("SELECT id FROM categories WHERE name = %s", (best,)).fetchone()
            if cat:
                conn.execute(
                    "UPDATE tech_names SET category_id = %s WHERE id = %s",
                    (cat["id"], row["id"]),
                )
                conn.execute(
                    "INSERT INTO category_keywords (category_id, keyword) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (cat["id"], row["canonical_name"].lower()),
                )
                count += 1
        conn.commit()
        return count

    def _flag_ambiguous_techs(self, conn: psycopg.Connection[Any]) -> int:
        result = conn.execute(
            "UPDATE tech_names SET ambiguous = TRUE "
            "WHERE ambiguous IS NULL "
            "AND LENGTH(canonical_name) <= 8 "
            "AND canonical_name ~ '^[A-Z][a-z]+$'"
        )
        count = result.rowcount or 0
        conn.commit()
        logger.info("Flagged %d new ambiguous tech names", count)
        return count

    def _remove_ambiguous_without_context(self, conn: psycopg.Connection[Any]) -> int:
        from src.categorization.ner import extract_tech_names

        rows = conn.execute(
            "SELECT m.id, m.name, m.description FROM mentions m "
            "JOIN tech_aliases ta ON ta.alias = LOWER(m.name) "
            "JOIN tech_names tn ON ta.tech_id = tn.id "
            "WHERE tn.ambiguous = TRUE"
        ).fetchall()

        to_delete = []
        for r in rows:
            extracted = extract_tech_names(r["description"] or "")
            if r["name"].lower() not in {e.lower() for e in extracted}:
                to_delete.append(r["id"])

        if to_delete:
            conn.execute("DELETE FROM mentions WHERE id = ANY(%s)", (to_delete,))
            conn.commit()
        logger.info("Removed %d ambiguous mentions without tech context", len(to_delete))
        return len(to_delete)

    def _remove_invalid_tech_predictions(self, conn: psycopg.Connection[Any]) -> int:
        from src.categorization.stopwords import is_valid_tech_name

        rows = conn.execute("SELECT id, name FROM predictions").fetchall()
        to_delete = [r["id"] for r in rows if not is_valid_tech_name(r["name"])]
        if to_delete:
            conn.execute("DELETE FROM predictions WHERE id = ANY(%s)", (to_delete,))
            conn.commit()
        logger.info("Removed %d invalid tech predictions", len(to_delete))
        return len(to_delete)


if __name__ == "__main__":
    from dotenv import load_dotenv

    from src.infra.config import Config

    load_dotenv()
    config = Config.from_env()
    cleaner = DataCleaner(config.database_url)
    result = cleaner.run()
    print(result)
