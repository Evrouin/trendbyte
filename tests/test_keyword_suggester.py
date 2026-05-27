"""Tests for keyword suggester."""

from unittest.mock import patch

from src.analysis.keyword_suggester import KeywordSuggester
from src.categorization.categorizer import Categorizer
from src.models import Mention


@patch("src.analysis.classifier.predict_proba", side_effect=Exception("no model"))
def test_suggests_frequent_uncategorized(_mock) -> None:
    cat = Categorizer()
    suggester = KeywordSuggester(cat, min_occurrences=2)

    mentions = [
        Mention(source="github", name="Xyzzy123", url="", description=""),
        Mention(source="devto", name="Xyzzy123", url="", description=""),
        Mention(source="hackernews", name="Xyzzy123", url="", description=""),
    ]

    suggestions = suggester.suggest(mentions)
    assert len(suggestions) == 1
    assert suggestions[0].keyword == "xyzzy123"
    assert suggestions[0].occurrences == 3


def test_ignores_infrequent() -> None:
    cat = Categorizer()
    suggester = KeywordSuggester(cat, min_occurrences=3)

    mentions = [
        Mention(source="github", name="RareThing", url="", description=""),
    ]

    suggestions = suggester.suggest(mentions)
    assert len(suggestions) == 0


def test_ignores_already_categorized() -> None:
    cat = Categorizer()
    suggester = KeywordSuggester(cat, min_occurrences=1)

    mentions = [
        Mention(source="github", name="React", url="", description=""),
        Mention(source="devto", name="React", url="", description=""),
        Mention(source="hackernews", name="React", url="", description=""),
    ]

    suggestions = suggester.suggest(mentions)
    assert len(suggestions) == 0
