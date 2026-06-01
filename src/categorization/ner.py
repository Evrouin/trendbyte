"""Tech name extraction using spaCy NER + whitelist fallback."""

from __future__ import annotations

import spacy
from spacy.language import Language

from src.categorization.stopwords import KNOWN_TECH, is_valid_tech_name

_nlp: Language | None = None


def _get_nlp() -> Language:
    """Load spaCy model with custom tech entity ruler."""
    global _nlp
    if _nlp is not None:
        return _nlp

    _nlp = spacy.load("en_core_web_sm")

    ruler = _nlp.add_pipe("entity_ruler", before="ner")
    patterns = [{"label": "TECH", "pattern": tech} for tech in KNOWN_TECH]
    patterns += [{"label": "TECH", "pattern": tech.capitalize()} for tech in KNOWN_TECH]
    patterns += [
        {"label": "TECH", "pattern": tech.upper()} for tech in KNOWN_TECH if len(tech) <= 4
    ]
    ruler.add_patterns(patterns)  # type: ignore[attr-defined]

    return _nlp


def extract_tech_names(text: str) -> list[str]:
    """Extract technology names from text using NER + whitelist."""
    if not text:
        return []

    cleaned = text.replace("r/", "subreddit_").replace("R/", "subreddit_")

    nlp = _get_nlp()
    doc = nlp(cleaned)

    names: list[str] = []
    for ent in doc.ents:
        if (
            ent.label_ == "TECH"
            or ent.label_ in ("ORG", "PRODUCT")
            and is_valid_tech_name(ent.text)
        ):
            if ent.text.lower() == "subreddit":
                continue
            names.append(ent.text)

    seen: set[str] = set()
    unique: list[str] = []
    for name in names:
        lower = name.lower()
        if lower not in seen:
            seen.add(lower)
            unique.append(name)

    return unique


def extract_best_tech_name(text: str) -> str:
    """Extract the single most relevant tech name from text."""
    names = extract_tech_names(text)
    return names[0] if names else ""
