"""Name normalization for cross-source deduplication."""

from __future__ import annotations

import re

# Common aliases mapping to canonical names
ALIASES: dict[str, str] = {
    "golang": "go",
    "js": "javascript",
    "ts": "typescript",
    "node": "nodejs",
    "react.js": "react",
    "reactjs": "react",
    "vue.js": "vue",
    "vuejs": "vue",
    "next.js": "nextjs",
    "nuxt.js": "nuxtjs",
    "deno2": "deno",
    "gpt-4": "gpt4",
    "gpt-5": "gpt5",
    "llama3": "llama",
    "llama-3": "llama",
}


def normalize(name: str) -> str:
    """Normalize a technology name for consistent grouping."""
    cleaned = re.sub(r"[^\w\s\-.]", "", name.strip().lower())
    cleaned = re.sub(r"\s+", "-", cleaned)
    return ALIASES.get(cleaned, cleaned)
