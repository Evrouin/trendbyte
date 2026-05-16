"""Technology categorization."""

from __future__ import annotations

CATEGORIES: dict[str, set[str]] = {
    "ai": {
        "ai", "ml", "llm", "gpt", "gpt4", "gpt5", "openai", "claude", "gemini",
        "langchain", "ollama", "llama", "mistral", "huggingface", "pytorch",
        "tensorflow", "transformers", "diffusion", "stable-diffusion", "midjourney",
        "copilot", "cursor", "neural", "deeplearning", "machinelearning",
    },
    "web": {
        "react", "nextjs", "vue", "nuxtjs", "svelte", "angular", "astro",
        "remix", "tailwind", "css", "html", "javascript", "typescript",
        "nodejs", "deno", "bun", "vite", "webpack", "htmx", "hono",
    },
    "devops": {
        "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins",
        "github-actions", "ci", "cd", "aws", "gcp", "azure", "vercel",
        "railway", "fly", "nix", "nixos", "linux", "nginx", "caddy",
    },
    "languages": {
        "rust", "go", "python", "zig", "elixir", "kotlin", "swift",
        "java", "csharp", "ruby", "haskell", "ocaml", "gleam", "mojo",
    },
    "databases": {
        "postgres", "postgresql", "mysql", "sqlite", "redis", "mongodb",
        "supabase", "neon", "turso", "drizzle", "prisma", "duckdb",
    },
    "security": {
        "security", "auth", "oauth", "encryption", "vulnerability", "cve",
        "firewall", "pentest", "cybersecurity", "zero-trust",
    },
}


def categorize(name: str) -> list[str]:
    """Return list of categories a technology belongs to."""
    normalized = name.lower().strip()
    matches = []
    for category, keywords in CATEGORIES.items():
        if normalized in keywords:
            matches.append(category)
    return matches if matches else ["other"]
