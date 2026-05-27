"""Tests for display name normalization."""

from src.categorization.display_names import to_display_name


def test_lowercase_to_display():
    assert to_display_name("python") == "Python"
    assert to_display_name("javascript") == "JavaScript"
    assert to_display_name("typescript") == "TypeScript"


def test_case_insensitive():
    assert to_display_name("PYTHON") == "Python"
    assert to_display_name("JavaScript") == "JavaScript"
    assert to_display_name("c++") == "C++"


def test_aliases():
    assert to_display_name("golang") == "Go"
    assert to_display_name("k8s") == "Kubernetes"
    assert to_display_name("nodejs") == "Node.js"
    assert to_display_name("postgres") == "PostgreSQL"


def test_unknown_passthrough():
    assert to_display_name("SomeNewTech") == "SomeNewTech"
    assert to_display_name("unknownlib") == "unknownlib"
