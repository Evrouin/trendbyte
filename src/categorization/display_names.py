"""Canonical display names — loaded from JSON seed data."""

from __future__ import annotations

import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "display_names.json"
DISPLAY_NAMES: dict[str, str] = json.loads(_DATA_PATH.read_text()) if _DATA_PATH.exists() else {}


def to_display_name(name: str) -> str:
    from src.categorization.resolver import get_resolver

    result = get_resolver().resolve(name)
    if result is not None:
        return result
    return name
