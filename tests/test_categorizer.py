"""Tests for categorizer and rising stars."""

from src.analysis.rising_stars import RisingStarDetector
from src.categorizer import Categorizer
from src.models import Mention


def test_categorize_known_tech() -> None:
    cat = Categorizer()
    assert "ai" in cat.categorize("pytorch")
    assert "web" in cat.categorize("react")
    assert "devops" in cat.categorize("docker")


def test_categorize_unknown() -> None:
    cat = Categorizer()
    result = cat.categorize("somenewthing")
    assert isinstance(result, list)
    assert len(result) >= 1


def test_rising_star_new_multi_source() -> None:
    detector = RisingStarDetector(min_confidence=0.3)
    previous: list[Mention] = []
    current = [
        Mention(source="github", name="NewTool", url="http://x", description=""),
        Mention(source="hackernews", name="NewTool", url="http://x", description=""),
        Mention(source="devto", name="NewTool", url="http://x", description=""),
    ]
    stars = detector.detect(current, previous)
    assert len(stars) == 1
    assert stars[0].name == "NewTool"
    assert stars[0].confidence >= 0.5


def test_rising_star_ignores_low_signal() -> None:
    detector = RisingStarDetector(min_confidence=0.5)
    previous: list[Mention] = []
    current = [
        Mention(source="github", name="Meh", url="", description=""),
    ]
    stars = detector.detect(current, previous)
    assert len(stars) == 0
