"""
Dynamic theme management for Zoom Poll Analyzer.
Loads themes from JSON files and applies them dynamically.
"""

import json
from typing import Any, Dict

from .resource_paths import get_themes_dir


class ThemeManager:
    """Handle application themes loaded from JSON files"""

    def __init__(self, app_instance):
        self.app = app_instance
        self.current_theme = "system"
        self.themes_dir = get_themes_dir()
        self.available_themes = self._load_available_themes()

    def _load_available_themes(self) -> Dict[str, Dict[str, Any]]:
        """Load all available themes from JSON files"""
        themes = {}

        # Always add system theme
        themes["system"] = {
            "name": "System Default",
            "description": "Follow system theme preference",
            "colors": {},
        }

        print(f"DEBUG: Looking for themes in: {self.themes_dir}")
        if not self.themes_dir.exists():
            print(f"DEBUG: Themes directory does not exist: {self.themes_dir}")
            return themes

        # Load themes from JSON files
        for theme_file in self.themes_dir.glob("*.json"):
            try:
                with open(theme_file, encoding="utf-8") as f:
                    theme_data = json.load(f)
                    theme_key = theme_file.stem  # filename without extension
                    themes[theme_key] = theme_data
                    print(f"DEBUG: Loaded theme '{theme_key}' from {theme_file}")
            except Exception as e:
                print(f"Warning: Could not load theme from {theme_file}: {e}")

        return themes

    def get_available_themes(self) -> Dict[str, str]:
        """Get available themes as dict {key: display_name}"""
        return {
            key: theme.get("name", key.title())
            for key, theme in self.available_themes.items()
        }

    def apply_theme(self, theme_name):
        """Apply the specified theme"""
        self.current_theme = theme_name

        if theme_name == "system":
            # Detect system theme and apply corresponding theme
            system_theme = self.detect_system_theme()
            if system_theme in self.available_themes:
                self._apply_theme_colors(self.available_themes[system_theme])
            else:
                # Fallback to light if system theme not available
                self._apply_theme_colors(self.available_themes.get("light", {}))
        elif theme_name in self.available_themes:
            self._apply_theme_colors(self.available_themes[theme_name])
        else:
            print(f"Warning: Theme '{theme_name}' not found, using light theme")
            self._apply_theme_colors(self.available_themes.get("light", {}))

    def _apply_theme_colors(self, theme_data: Dict[str, Any]):
        """Apply theme colors to generate stylesheet"""
        colors = theme_data.get("colors", {})

        if not colors:
            print("Warning: No colors defined in theme, using default stylesheet")
            self.app.setStyleSheet("")
            return

        stylesheet = self._generate_stylesheet(colors)
        self.app.setStyleSheet(stylesheet)
        print(f"DEBUG: Applied theme with {len(colors)} color definitions")

    def _generate_stylesheet(self, colors: Dict[str, str]) -> str:
        """Generate complete stylesheet from color definitions"""
        return f"""
        QMainWindow {{
            background-color: {colors.get("primary_background", "#f5f5f5")};
            color: {colors.get("primary_text", "#333333")};
        }}

        QWidget {{
            background-color: {colors.get("primary_background", "#f5f5f5")};
            color: {colors.get("primary_text", "#333333")};
        }}

        QTabWidget::pane {{
            border: 1px solid {colors.get("border", "#cccccc")};
            background-color: {colors.get("widget_background", "#ffffff")};
        }}

        QTabBar::tab {{
            background-color: {colors.get("tab_background", "#e0e0e0")};
            color: {colors.get("tab_text", "#333333")};
            border: 1px solid {colors.get("border", "#cccccc")};
            padding: 6px 12px;
            margin-right: 2px;
        }}

        QTabBar::tab:selected {{
            background-color: {colors.get("tab_selected_background", "#ffffff")};
            border-bottom: 1px solid {colors.get("tab_selected_background", "#ffffff")};
        }}

        QTabBar::tab:hover {{
            background-color: {colors.get("tab_hover_background", "#f0f0f0")};
        }}

        QTableWidget {{
            background-color: {colors.get("widget_background", "#ffffff")};
            alternate-background-color: {colors.get("alternate_background", "#f9f9f9")};
            color: {colors.get("widget_text", "#333333")};
            gridline-color: {colors.get("grid_line", "#e0e0e0")};
            border: 1px solid {colors.get("border", "#cccccc")};
            selection-background-color: {colors.get("selected_background", "#0078d4")};
            selection-color: {colors.get("selected_text", "#ffffff")};
        }}

        QTableWidget::item {{
            border: none;
            padding: 2px;
        }}

        QTableWidget::item:selected {{
            background-color: {colors.get("selected_background", "#0078d4")};
            color: {colors.get("selected_text", "#ffffff")};
        }}

        QTableWidget::item:hover {{
            background-color: {colors.get("hover_background", "#e6f3ff")};
            color: {colors.get("hover_text", "#333333")};
        }}

        QHeaderView::section {{
            background-color: {colors.get("header_background", "#f0f0f0")};
            color: {colors.get("header_text", "#333333")};
            border: 1px solid {colors.get("border", "#cccccc")};
            padding: 4px;
            font-weight: bold;
        }}

        QHeaderView::section:hover {{
            background-color: {colors.get("hover_background", "#e6f3ff")};
        }}

        QPushButton {{
            background-color: {colors.get("button_background", "#ffffff")};
            color: {colors.get("button_text", "#333333")};
            border: 1px solid {colors.get("button_border", "#cccccc")};
            padding: 6px 12px;
            border-radius: 3px;
            min-width: 60px;
        }}

        QPushButton:hover {{
            background-color: {colors.get("button_hover_background", "#f0f0f0")};
        }}

        QPushButton:pressed {{
            background-color: {colors.get("button_pressed_background", "#e0e0e0")};
        }}

        QPushButton:disabled {{
            background-color: {colors.get("alternate_background", "#f9f9f9")};
            color: {colors.get("border", "#cccccc")};
        }}

        QLineEdit, QSpinBox, QComboBox {{
            background-color: {colors.get("input_background", "#ffffff")};
            color: {colors.get("input_text", "#333333")};
            border: 1px solid {colors.get("input_border", "#cccccc")};
            padding: 4px;
            border-radius: 2px;
        }}

        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
            border: 2px solid {colors.get("input_focus_border", "#0078d4")};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}

        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {colors.get("input_text", "#333333")};
            margin-right: 5px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {colors.get("widget_background", "#ffffff")};
            color: {colors.get("widget_text", "#333333")};
            border: 1px solid {colors.get("border", "#cccccc")};
            selection-background-color: {colors.get("selected_background", "#0078d4")};
            selection-color: {colors.get("selected_text", "#ffffff")};
        }}

        QCheckBox {{
            color: {colors.get("widget_text", "#333333")};
            spacing: 8px;
        }}

        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {colors.get("input_border", "#cccccc")};
            background-color: {colors.get("input_background", "#ffffff")};
        }}

        QCheckBox::indicator:checked {{
            background-color: {colors.get("selected_background", "#0078d4")};
            border: 1px solid {colors.get("selected_background", "#0078d4")};
        }}

        QLabel {{
            color: {colors.get("widget_text", "#333333")};
        }}

        QGroupBox {{
            color: {colors.get("widget_text", "#333333")};
            border: 1px solid {colors.get("border", "#cccccc")};
            border-radius: 3px;
            margin-top: 10px;
            padding-top: 10px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
            background-color: {colors.get("primary_background", "#f5f5f5")};
        }}

        QMenuBar {{
            background-color: {colors.get("primary_background", "#f5f5f5")};
            color: {colors.get("primary_text", "#333333")};
            border-bottom: 1px solid {colors.get("border", "#cccccc")};
        }}

        QMenuBar::item {{
            background-color: transparent;
            padding: 4px 8px;
        }}

        QMenuBar::item:selected {{
            background-color: {colors.get("hover_background", "#e6f3ff")};
        }}

        QMenu {{
            background-color: {colors.get("menu_background", "#ffffff")};
            color: {colors.get("menu_text", "#333333")};
            border: 1px solid {colors.get("border", "#cccccc")};
        }}

        QMenu::item {{
            padding: 6px 16px;
        }}

        QMenu::item:selected {{
            background-color: {colors.get("menu_selected_background", "#0078d4")};
            color: {colors.get("menu_selected_text", "#ffffff")};
        }}

        QStatusBar {{
            background-color: {colors.get("status_bar_background", "#f0f0f0")};
            color: {colors.get("status_bar_text", "#333333")};
            border-top: 1px solid {colors.get("status_bar_border", "#cccccc")};
        }}

        QStatusBar QLabel {{
            color: {colors.get("status_bar_text", "#333333")};
            padding: 0px;
            margin: 0px;
        }}

        QProgressBar {{
            border: 1px solid {colors.get("border", "#cccccc")};
            background-color: {colors.get("progress_bar_background", "#e0e0e0")};
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {colors.get("progress_bar_chunk", "#0078d4")};
        }}

        QDialog {{
            background-color: {colors.get("dialog_background", "#f5f5f5")};
            color: {colors.get("dialog_text", "#333333")};
        }}

        QMessageBox {{
            background-color: {colors.get("dialog_background", "#f5f5f5")};
            color: {colors.get("dialog_text", "#333333")};
        }}

        QSplitter::handle {{
            background-color: {colors.get("splitter_handle", "#cccccc")};
        }}
        """

    def detect_system_theme(self):
        """Detect system theme preference"""
        try:
            # Windows detection
            import winreg

            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(
                registry,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "light" if value else "dark"
        except Exception:
            try:
                # macOS detection
                import subprocess

                result = subprocess.run(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"],  # noqa: S607
                    capture_output=True,
                    text=True,
                )
                return "dark" if "Dark" in result.stdout else "light"
            except Exception:
                try:
                    # Linux detection (GNOME/KDE)
                    import subprocess

                    result = subprocess.run(
                        [  # noqa: S607
                            "gsettings",
                            "get",
                            "org.gnome.desktop.interface",
                            "gtk-theme",
                        ],
                        capture_output=True,
                        text=True,
                    )
                    return "dark" if "dark" in result.stdout.lower() else "light"
                except Exception:
                    # Default to light if detection fails
                    return "light"

    def is_dark_theme(self):
        """Check if current effective theme is dark"""
        if self.current_theme == "system":
            return self.detect_system_theme() == "dark"
        return self.current_theme == "dark"

    def get_current_theme_colors(self) -> Dict[str, str]:
        """Get colors from current active theme"""
        if self.current_theme == "system":
            # Get system theme and return its colors
            system_theme = self.detect_system_theme()
            if system_theme in self.available_themes:
                return self.available_themes[system_theme].get("colors", {})
            else:
                return self.available_themes.get("light", {}).get("colors", {})
        elif self.current_theme in self.available_themes:
            return self.available_themes[self.current_theme].get("colors", {})
        else:
            return self.available_themes.get("light", {}).get("colors", {})

    def reload_themes(self):
        """Reload themes from JSON files (useful for development)"""
        self.available_themes = self._load_available_themes()
        return self.get_available_themes()
