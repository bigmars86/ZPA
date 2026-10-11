"""
Resource path utilities for PyInstaller compatibility.
Handles different path resolution for development vs executable environments.
"""

import sys
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """
    Get the absolute path to a resource file.
    Works in both development and PyInstaller executable environments.

    Args:
        relative_path: Path relative to the src/zpa/ directory

    Returns:
        Absolute Path object to the resource
    """
    if getattr(sys, "frozen", False):
        # Running as PyInstaller executable
        if hasattr(sys, "_MEIPASS"):
            # PyInstaller creates a temporary folder and stores path in _MEIPASS
            base_path = Path(sys._MEIPASS)
        else:
            # Fallback for other frozen environments
            base_path = Path(sys.executable).parent
    else:
        # Running in development environment
        # Go up from src/zpa/utils/ to src/zpa/
        base_path = Path(__file__).parent.parent

    return base_path / relative_path


def get_themes_dir() -> Path:
    """Get the themes directory path."""
    return get_resource_path("resources/themes")


def get_translations_dir() -> Path:
    """Get the translations directory path."""
    return get_resource_path("resources/translations")


def get_icons_dir() -> Path:
    """Get the icons directory path."""
    return get_resource_path("resources/icons")


def get_config_file_path(ini_filename: str = "zpa.ini") -> Path:
    """
    Get the configuration file path.
    In executable mode, look for INI file next to the executable.
    In development mode, look in the project root.

    This function implements a hybrid approach:
    1. If bundled template exists inside executable, copy it to external location first time
    2. Always use external location for read/write operations (writable)
    """
    print(f"DEBUG: get_config_file_path called with ini_filename: {ini_filename}")

    if getattr(sys, "frozen", False):
        # Running as executable - always use external location (writable)
        exe_dir = Path(sys.executable).parent
        external_ini = exe_dir / ini_filename

        # If external INI doesn't exist, try to copy from bundled template
        if not external_ini.exists() and hasattr(sys, "_MEIPASS"):
            bundled_ini = Path(sys._MEIPASS) / ini_filename
            if bundled_ini.exists():
                try:
                    import shutil

                    shutil.copy2(bundled_ini, external_ini)
                except Exception as e:
                    print(f"DEBUG: Failed to copy bundled template: {e}")

        return external_ini
    else:
        # Development mode - look in project root (3 levels up from src/zpa/utils/)
        project_root = Path(__file__).parent.parent.parent.parent
        ini_path = project_root / ini_filename
        return ini_path


def is_frozen() -> bool:
    """Check if running as PyInstaller executable."""
    return getattr(sys, "frozen", False)


def get_application_dir() -> Path:
    """Get the application directory (where the exe is located or project root)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent.parent.parent
