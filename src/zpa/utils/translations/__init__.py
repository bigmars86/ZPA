"""
Translation management for Zoom Poll Analyzer.
"""

import json
from pathlib import Path

__all__ = ["Translations"]


class Translations:
    """Handle multi-language support"""

    LANGUAGES = {"en": "English", "de": "Deutsch", "el": "Ελληνικά"}

    def __init__(self, language="en"):
        self.current_language = language
        self.translations_dir = Path(__file__).parent
        self._translations_cache = {}
        self._load_translations()

    def _load_translations(self):
        """Load all translation files"""
        print(f"Debug: Loading translations from: {self.translations_dir}")
        for lang_code in self.LANGUAGES.keys():
            translation_file = self.translations_dir / f"{lang_code}.json"
            print(f"Debug: Checking translation file: {translation_file}")
            if translation_file.exists():
                try:
                    with open(translation_file, encoding="utf-8") as f:
                        self._translations_cache[lang_code] = json.load(f)
                        print(
                            f"Debug: Loaded {len(self._translations_cache[lang_code])} translations for {lang_code}"
                        )
                except Exception as e:
                    print(f"Warning: Could not load translations for {lang_code}: {e}")
                    self._translations_cache[lang_code] = {}
            else:
                print(f"Warning: Translation file not found: {translation_file}")
                self._translations_cache[lang_code] = {}

    def get(self, key, default=None):
        """Get translation for current language"""
        # Try current language first
        translation = self._translations_cache.get(self.current_language, {}).get(key)
        if translation is not None:
            return translation

        # Fall back to English
        translation = self._translations_cache.get("en", {}).get(key)
        if translation is not None:
            return translation

        # Return default or key itself
        return default or key

    def set_language(self, language):
        """Set current language"""
        if language in self.LANGUAGES:
            self.current_language = language
