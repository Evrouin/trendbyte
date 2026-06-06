"""Database-driven tech name resolver with in-memory cache."""

from __future__ import annotations

import psycopg


class TechResolver:
    def __init__(self, database_url: str | None = None) -> None:
        self._database_url = database_url
        self._cache: dict[str, str] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if self._database_url:
            try:
                with psycopg.connect(self._database_url) as conn:
                    rows = conn.execute(
                        "SELECT ta.alias, tn.canonical_name "
                        "FROM tech_aliases ta JOIN tech_names tn ON ta.tech_id = tn.id"
                    ).fetchall()
                self._cache = {row[0].lower(): row[1] for row in rows}
                if self._cache:
                    return
            except Exception:
                pass
        self._seed_from_static()

    def _seed_from_static(self) -> None:
        import json
        from pathlib import Path

        data_dir = Path(__file__).parent.parent.parent / "data"
        dn_path = data_dir / "display_names.json"
        kt_path = data_dir / "known_tech.json"
        al_path = data_dir / "aliases.json"

        if dn_path.exists():
            for alias, canonical in json.loads(dn_path.read_text()).items():
                self._cache[alias.lower()] = canonical
        if kt_path.exists():
            for tech in json.loads(kt_path.read_text()):
                if tech.lower() not in self._cache:
                    self._cache[tech.lower()] = tech
        if al_path.exists():
            for alias, target in json.loads(al_path.read_text()).items():
                if alias.lower() not in self._cache:
                    self._cache[alias.lower()] = self._cache.get(target, target)

    def resolve(self, name: str) -> str | None:
        return self._cache.get(name.lower().strip())

    def get_all_aliases(self) -> set[str]:
        return set(self._cache.keys())

    def add_alias(self, canonical_name: str, alias: str, source: str = "learned") -> None:
        with psycopg.connect(self._database_url) as conn:
            row = conn.execute(
                "SELECT id FROM tech_names WHERE canonical_name = %s", (canonical_name,)
            ).fetchone()
            if row is None:
                return
            conn.execute(
                "INSERT INTO tech_aliases (tech_id, alias, source) VALUES (%s, %s, %s) "
                "ON CONFLICT (alias) DO NOTHING",
                (row[0], alias.lower(), source),
            )
        self._cache[alias.lower()] = canonical_name

    def refresh(self) -> None:
        self._load_cache()


_resolver: TechResolver | None = None


def get_resolver() -> TechResolver:
    global _resolver
    if _resolver is None:
        from src.infra.config import Config

        config = Config.from_env()
        _resolver = TechResolver(config.database_url)
    return _resolver
