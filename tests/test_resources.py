"""Consistency checks for the translation and theme files bundled with ZPA."""

import json
from pathlib import Path

import pytest

RESOURCES = Path(__file__).resolve().parents[1] / "src" / "zpa" / "resources"
TRANSLATIONS = sorted((RESOURCES / "translations").glob("*.json"))
THEMES = sorted((RESOURCES / "themes").glob("*.json"))


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", TRANSLATIONS, ids=lambda p: p.stem)
def test_translation_has_same_keys_as_english(path: Path) -> None:
    english = load(RESOURCES / "translations" / "en.json")
    assert set(load(path)) == set(english)


@pytest.mark.parametrize("path", THEMES, ids=lambda p: p.stem)
def test_theme_defines_all_colors(path: Path) -> None:
    reference = load(RESOURCES / "themes" / "light.json")
    theme = load(path)
    assert {"name", "description", "colors"} <= set(theme)
    assert set(theme["colors"]) == set(reference["colors"])
