"""
Zoom Poll Analyzer - A PyQt6 application for analyzing Zoom meeting poll results.

This package provides a complete GUI application for connecting to Zoom's API,
retrieving meeting poll data, and analyzing the results with export capabilities.

Main Features:
- Multi-language support (English, German, Greek)
- Dark/Light theme support with system theme detection
- Configurable settings with INI file persistence
- CSV export with UTF-8 encoding
- Real-time poll data analysis
- Cross-platform compatibility

Usage:
    python -m zpa

Classes:
    ZoomPollAnalyzer: Main application window
    SettingsManager: Handles application settings persistence
    ThemeManager: Manages application theming
    Translations: Handles multi-language support
    ZoomAPI: Zoom API client for data retrieval
"""

__version__ = "1.0.0"
__author__ = "Marcel Vilas"
__email__ = ""
__description__ = "A PyQt6 application for analyzing Zoom meeting poll results"

from .main import ZoomPollAnalyzer, main

__all__ = ["ZoomPollAnalyzer", "main"]
