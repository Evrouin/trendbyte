"""Technology categorization — DB-backed with dynamic keyword management."""

from __future__ import annotations

from typing import Any

from src.logger import Logger

logger = Logger.get(__name__)

DEFAULT_CATEGORIES: dict[str, set[str]] = {
    "ai": {
        "ai",
        "ml",
        "llm",
        "gpt",
        "gpt4",
        "gpt5",
        "openai",
        "claude",
        "gemini",
        "langchain",
        "ollama",
        "llama",
        "mistral",
        "huggingface",
        "pytorch",
        "tensorflow",
        "transformers",
        "diffusion",
        "stable-diffusion",
        "midjourney",
        "copilot",
        "cursor",
        "neural",
        "deeplearning",
        "machinelearning",
    },
    "web": {
        "react",
        "nextjs",
        "vue",
        "nuxtjs",
        "svelte",
        "angular",
        "astro",
        "remix",
        "tailwind",
        "css",
        "html",
        "javascript",
        "typescript",
        "nodejs",
        "deno",
        "bun",
        "vite",
        "webpack",
        "htmx",
        "hono",
    },
    "devops": {
        "docker",
        "kubernetes",
        "k8s",
        "terraform",
        "ansible",
        "jenkins",
        "github-actions",
        "ci",
        "cd",
        "aws",
        "gcp",
        "azure",
        "vercel",
        "railway",
        "fly",
        "nix",
        "nixos",
        "linux",
        "nginx",
        "caddy",
    },
    "languages": {
        "rust",
        "go",
        "python",
        "zig",
        "elixir",
        "kotlin",
        "swift",
        "java",
        "csharp",
        "ruby",
        "haskell",
        "ocaml",
        "gleam",
        "mojo",
    },
    "databases": {
        "postgres",
        "postgresql",
        "mysql",
        "sqlite",
        "redis",
        "mongodb",
        "supabase",
        "neon",
        "turso",
        "drizzle",
        "prisma",
        "duckdb",
    },
    "security": {
        "security",
        "auth",
        "oauth",
        "encryption",
        "vulnerability",
        "cve",
        "firewall",
        "pentest",
        "cybersecurity",
        "zero-trust",
    },
}


class Categorizer:
    """DB-backed categorizer with dynamic keyword management."""

    def __init__(self, db_conn: Any = None) -> None:
        self._conn = db_conn
        self._cache: dict[str, set[str]] | None = None

    def categorize(self, name: str) -> list[str]:
        """Return categories for a technology name."""
        categories = self._get_categories()
        normalized = name.lower().strip()
        matches = [cat for cat, keywords in categories.items() if normalized in keywords]
        return matches if matches else ["other"]

    def add_keyword(self, category: str, keyword: str) -> None:
        """Add a new keyword to a category."""
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
        logger.info("Added keyword '%s' to category '%s'", keyword, category)

    def add_category(self, name: str, keywords: list[str] | None = None) -> None:
        """Create a new category, optionally with initial keywords."""
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
        logger.info("Created category '%s' with %d keywords", name, len(keywords or []))

    def seed_defaults(self) -> None:
        """Populate DB with default categories and keywords."""
        if not self._conn:
            return
        for category, keywords in DEFAULT_CATEGORIES.items():
            self.add_category(category, list(keywords))
        logger.info("Seeded default categories")

    def _get_categories(self) -> dict[str, set[str]]:
        """Load categories from DB or fall back to defaults."""
        if self._cache:
            return self._cache

        if not self._conn:
            self._cache = DEFAULT_CATEGORIES
            return self._cache

        rows = self._conn.execute(
            "SELECT c.name as category, ck.keyword "
            "FROM categories c "
            "LEFT JOIN category_keywords ck ON c.id = ck.category_id"
        ).fetchall()

        if not rows or all(row["keyword"] is None for row in rows):
            self._cache = DEFAULT_CATEGORIES
            return self._cache

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
