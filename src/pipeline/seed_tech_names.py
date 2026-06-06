"""Seed tech_names and tech_aliases from existing data sources."""

from __future__ import annotations

import csv
import io

import psycopg
import requests

from src.categorization.display_names import DISPLAY_NAMES
from src.categorization.stopwords import KNOWN_TECH

STACKSHARE_URL = "https://raw.githubusercontent.com/captn3m0/stackshare-dataset/master/tools.csv"
RELEVANT_CATEGORIES = {
    "languages-and-frameworks",
    "libraries",
    "data-stores",
    "build-test-deploy",
    "application-hosting",
    "monitoring",
}


def _upsert_tech(conn: psycopg.Connection, canonical_name: str) -> int:
    row = conn.execute(
        "INSERT INTO tech_names (canonical_name) VALUES (%s) "
        "ON CONFLICT (canonical_name) DO UPDATE SET canonical_name = EXCLUDED.canonical_name "
        "RETURNING id",
        (canonical_name,),
    ).fetchone()
    return row[0]  # type: ignore[index]


def _add_alias(conn: psycopg.Connection, tech_id: int, alias: str, source: str) -> None:
    conn.execute(
        "INSERT INTO tech_aliases (tech_id, alias, source) VALUES (%s, %s, %s) "
        "ON CONFLICT (alias) DO NOTHING",
        (tech_id, alias.lower(), source),
    )


def _seed_display_names(conn: psycopg.Connection) -> None:
    for key, display in DISPLAY_NAMES.items():
        tech_id = _upsert_tech(conn, display)
        _add_alias(conn, tech_id, key, "display_names")
        if display.lower() != key:
            _add_alias(conn, tech_id, display.lower(), "display_names")


def _seed_known_tech(conn: psycopg.Connection) -> None:
    existing = {row[0] for row in conn.execute("SELECT canonical_name FROM tech_names").fetchall()}
    for tech in KNOWN_TECH:
        if tech not in {e.lower() for e in existing}:
            tech_id = _upsert_tech(conn, tech)
            _add_alias(conn, tech_id, tech, "known_tech")


def _seed_stackshare(conn: psycopg.Connection) -> None:
    print("Downloading StackShare dataset...")
    resp = requests.get(STACKSHARE_URL, timeout=60)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))

    tools = []
    for row in reader:
        cat = row.get("category_slug", "")
        if cat in RELEVANT_CATEGORIES:
            try:
                popularity = int(row.get("stacks_count", "0") or "0")
            except ValueError:
                popularity = 0
            tools.append((row.get("name", ""), popularity))

    tools.sort(key=lambda x: x[1], reverse=True)
    tools = tools[:3000]

    existing_canonical = {
        row[0].lower() for row in conn.execute("SELECT canonical_name FROM tech_names").fetchall()
    }

    added = 0
    for name, _ in tools:
        if not name:
            continue
        if name.lower() in existing_canonical:
            row = conn.execute(
                "SELECT id FROM tech_names WHERE LOWER(canonical_name) = %s",
                (name.lower(),),
            ).fetchone()
            if row:
                _add_alias(conn, row[0], name.lower(), "stackshare")
        else:
            tech_id = _upsert_tech(conn, name)
            _add_alias(conn, tech_id, name.lower(), "stackshare")
            existing_canonical.add(name.lower())
            added += 1

    print(f"StackShare: added {added} new techs, processed {len(tools)} tools total")


def seed(database_url: str) -> None:
    with psycopg.connect(database_url) as conn:
        _seed_display_names(conn)
        _seed_known_tech(conn)
        print(f"Seeded {len(DISPLAY_NAMES)} display_names + {len(KNOWN_TECH)} known_tech entries")
        _seed_stackshare(conn)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(".env.prod")

    import os

    database_url = os.environ["DATABASE_URL"]
    seed(database_url)
