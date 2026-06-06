"""Technology categorization — DB-backed."""

from __future__ import annotations

from typing import Any

from src.infra.logger import Logger

logger = Logger.get(__name__)


class Categorizer:
    def __init__(self, db_conn: Any = None) -> None:
        self._conn = db_conn
        self._cache: dict[str, set[str]] | None = None

    def categorize(self, name: str) -> list[str]:
        categories = self._get_categories()
        normalized = name.lower().strip()
        matches = [cat for cat, keywords in categories.items() if normalized in keywords]
        if matches:
            return matches
        try:
            from src.analysis.classifier import predict_proba

            proba = predict_proba(normalized)
            if proba:
                best = max(proba, key=proba.get)
                if proba[best] > 0.4:
                    return [best]
        except Exception:
            pass
        return ["other"]

    def add_keyword(self, category: str, keyword: str) -> None:
        if not self._conn:
            return
        self._conn.execute(
            "INSERT INTO category_keywords (category_id, keyword) "
            "SELECT id, %s FROM categories WHERE name = %s "
            "ON CONFLICT DO NOTHING",
            (keyword.lower(), category.lower()),
        )
        self._conn.commit()
        self._cache = None

    def add_category(self, name: str, keywords: list[str] | None = None) -> None:
        if not self._conn:
            return
        self._conn.execute(
            "INSERT INTO categories (name) VALUES (%s) ON CONFLICT DO NOTHING",
            (name.lower(),),
        )
        if keywords:
            for kw in keywords:
                self.add_keyword(name, kw)
        self._conn.commit()
        self._cache = None

    def _get_categories(self) -> dict[str, set[str]]:
        if self._cache:
            return self._cache

        if not self._conn:
            self._cache = {}
            return self._cache

        rows = self._conn.execute(
            "SELECT c.name as category, ck.keyword "
            "FROM categories c "
            "LEFT JOIN category_keywords ck ON c.id = ck.category_id"
        ).fetchall()

        result: dict[str, set[str]] = {}
        for row in rows:
            cat = row["category"]
            kw = row["keyword"]
            if cat not in result:
                result[cat] = set()
            if kw:
                result[cat].add(kw)

        self._cache = result
        return self._cache
