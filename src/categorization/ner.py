"""Tech name extraction using spaCy NER + database-driven aliases."""

from __future__ import annotations

from pathlib import Path

import spacy
from spacy.language import Language

from src.categorization.resolver import get_resolver

_nlp: Language | None = None
_MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "ner_model"


def _get_tech_patterns() -> set[str]:
    return get_resolver().get_all_aliases()


def _get_nlp() -> Language:
    global _nlp
    if _nlp is not None:
        return _nlp

    if _MODEL_PATH.exists():
        _nlp = spacy.load(_MODEL_PATH)
        return _nlp

    _nlp = spacy.load("en_core_web_sm")

    tech_list = _get_tech_patterns()
    ruler = _nlp.add_pipe("entity_ruler", before="ner")
    patterns = [{"label": "TECH", "pattern": tech} for tech in tech_list]
    patterns += [{"label": "TECH", "pattern": tech.capitalize()} for tech in tech_list]
    patterns += [{"label": "TECH", "pattern": tech.upper()} for tech in tech_list if len(tech) <= 4]
    ruler.add_patterns(patterns)  # type: ignore[attr-defined]

    return _nlp


def extract_tech_names(text: str) -> list[str]:
    """Extract technology names from text using NER + whitelist."""
    if not text:
        return []

    cleaned = text.replace("r/", "subreddit_").replace("R/", "subreddit_")

    nlp = _get_nlp()
    doc = nlp(cleaned)

    resolver = get_resolver()
    names: list[str] = []
    for ent in doc.ents:
        if (
            ent.label_ == "TECH"
            or ent.label_ in ("ORG", "PRODUCT")
            and resolver.resolve(ent.text) is not None
        ):
            if ent.text.lower() == "subreddit":
                continue
            if len(ent) == 1 and ent[0].pos_ in ("VERB", "AUX", "ADV", "DET", "PRON", "ADP"):
                continue
            if len(ent.text) < 2:
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
