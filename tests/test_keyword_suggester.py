"""Tests for keyword suggester."""

from src.analysis.keyword_suggester import KeywordSuggester
from src.categorizer import Categorizer
from src.models import Mention


def test_suggests_frequent_uncategorized() -> None:
    cat = Categorizer()
    suggester = KeywordSuggester(cat, min_occurrences=2)

    mentions = [
        Mention(source="github", name="NewFramework", url="", description="a web framework"),
        Mention(source="devto", name="NewFramework", url="", description="frontend framework"),
        Mention(source="hackernews", name="NewFramework", url="", description="build apps"),
    ]

    suggestions = suggester.suggest(mentions)
    assert len(suggestions) == 1
    assert suggestions[0].keyword == "newframework"
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
