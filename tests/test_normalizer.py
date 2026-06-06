"""Tests for name normalization."""

from src.categorization.normalizer import normalize


def test_lowercase() -> None:
    assert normalize("Rust") == "rust"


def test_strips_special_chars() -> None:
    assert normalize("React!") == "react"


def test_aliases_resolved() -> None:
    assert normalize("Golang") == "go"
    assert normalize("JS") == "javascript"
    assert normalize("Vue.js") == "vue"
    assert normalize("Node") == "node.js"


def test_spaces_to_dashes() -> None:
    assert normalize("Visual Studio") == "visual-studio"
