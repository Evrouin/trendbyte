"""Filter out common words that aren't technology names."""

from __future__ import annotations

STOP_WORDS: set[str] = {
    "i", "a", "an", "the", "this", "that", "it", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "can", "shall", "must",
    "my", "your", "his", "her", "its", "our", "their", "we", "they", "you",
    "me", "him", "us", "them", "who", "what", "which", "when", "where", "why",
    "how", "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "no", "not", "only", "own", "same", "so", "than", "too",
    "very", "just", "because", "as", "until", "while", "of", "at", "by",
    "for", "with", "about", "against", "between", "through", "during",
    "before", "after", "above", "below", "to", "from", "up", "down", "in",
    "out", "on", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "all", "and", "but", "or", "nor", "if", "else",
    "new", "old", "big", "small", "long", "short", "high", "low", "good",
    "bad", "great", "best", "worst", "first", "last", "next", "many",
    "much", "little", "less", "least", "still", "also", "even", "now",
    "today", "yesterday", "tomorrow", "never", "always", "sometimes",
    "project", "local", "hardware", "software", "update", "release",
    "version", "part", "way", "thing", "things", "people", "time",
    "year", "years", "day", "days", "week", "month", "world", "life",
    "work", "home", "case", "point", "fact", "issue", "problem",
    "question", "answer", "idea", "plan", "story", "show", "try",
    "ask", "need", "want", "look", "use", "find", "give", "tell",
    "think", "say", "make", "know", "take", "see", "come", "get",
    "like", "love", "hate", "help", "start", "stop", "run", "open",
    "close", "read", "write", "learn", "build", "built", "made",
    "why", "how", "what", "when", "where", "who", "which",
    "don't", "doesn't", "didn't", "won't", "wouldn't", "can't",
    "couldn't", "shouldn't", "isn't", "aren't", "wasn't", "weren't",
    # Non-tech nouns that appear in titles
    "zero", "one", "two", "three", "four", "five", "ten", "hundred",
    "company", "team", "user", "users", "developer", "developers",
    "code", "data", "system", "systems", "server", "app", "apps",
    "file", "files", "page", "site", "web", "internet", "network",
    "game", "games", "mod", "menu", "free", "download", "tool", "tools",
    "guide", "tutorial", "introduction", "overview", "review", "comparison",
    "announcement", "attestation", "bambu", "gutenberg", "yellow", "key",
    "anything", "everything", "nothing", "something", "someone", "anyone",
    "real", "simple", "full", "complete", "modern", "better", "faster",
    "inside", "outside", "behind", "beyond", "across", "along",
}

MIN_NAME_LENGTH = 3


def is_valid_tech_name(name: str) -> bool:
    """Check if a name is likely a real technology/tool name."""
    cleaned = name.lower().strip()
    if len(cleaned) < MIN_NAME_LENGTH:
        return False
    if cleaned in STOP_WORDS:
        return False
    if cleaned.isdigit():
        return False
    # Reject long hyphenated slugs (likely repo names, not tech names)
    if cleaned.count("-") >= 3:
        return False
    return True
