"""Known tech names — loaded from JSON seed data."""

from __future__ import annotations

import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "known_tech.json"
KNOWN_TECH: set[str] = set(json.loads(_DATA_PATH.read_text())) if _DATA_PATH.exists() else set()


def is_valid_tech_name(name: str) -> bool:
    from src.categorization.resolver import get_resolver

    cleaned = name.lower().strip()
    if len(cleaned) < 2:
        return False
    return get_resolver().resolve(cleaned) is not None


def is_valid_language(name: str) -> bool:
    cleaned = name.lower().strip()
    if len(cleaned) < 2:
        return False
    if cleaned.isdigit():
        return False
    return True
