"""Name normalization for cross-source deduplication."""

from __future__ import annotations

import json
import re
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "aliases.json"
ALIASES: dict[str, str] = json.loads(_DATA_PATH.read_text()) if _DATA_PATH.exists() else {}


def normalize(name: str) -> str:
    cleaned = re.sub(r"[^\w\s\-.]", "", name.strip().lower())
    cleaned = re.sub(r"\s+", "-", cleaned)
    from src.categorization.resolver import get_resolver

    result = get_resolver().resolve(cleaned)
    return result.lower() if result else cleaned
