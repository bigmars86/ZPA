"""
Settings management for Zoom Poll Analyzer.
Handles INI file persistence and default values.
"""

import configparser
from pathlib import Path
from typing import List

from .resource_paths import get_config_file_path


class SettingsManager:
    """Manage settings persistence using INI file"""

    def __init__(self, ini_path=None):
        if ini_path:
            self.config_file = Path(ini_path)
        else:
            # Use resource path utility for proper INI file location
            self.config_file = get_config_file_path()

        print(f"DEBUG: Settings manager using config file: {self.config_file}")

        self.config = configparser.ConfigParser()
        self._loaded_from_disk = False
        self.load_default_settings()
        self.load_settings()

    def load_default_settings(self):
        """Load default settings"""
        # Note: No secrets stored in code - these will be empty by default
        self.config["Zoom"] = {
            "account_id": "",
            "client_id": "",
            "client_secret": "",
            "meeting_id": "",
        }

        self.config["UI"] = {
            "language": "en",
            "theme": "system",
            "max_height": "600",
            "font_size": "8",  # Table/data font
            "ui_font_size": "9",  # UI controls, dialogs, tabs
        }

        self.config["Application"] = {
            "debug": "false",
            "exclude_names": "",
            "poll_question": "",  # Poll question filter
            "ini_location": str(self.config_file),
        }

        self.config["Export"] = {
            "format": "csv",  # Default export format
            "separator": ";",  # Default to semicolon for Excel compatibility
        }

        self.config["Network"] = {
            "proxy": "",  # Optional HTTP/HTTPS proxy, e.g. http://host:8080
            "proxy_autodetect": "true",  # Use the OS/system proxy settings automatically
        }

        self.config["Email"] = {
            "smtp_server": "",
            "smtp_port": "587",
            "smtp_username": "",
            "smtp_password": "",
            "smtp_use_tls": "true",
            "recipients": "",
        }

    def load_settings(self):
        """Load settings from INI file (reads disk only once) and return as dictionary"""
        if not self._loaded_from_disk:
            if self.config_file.exists():
                print(f"DEBUG: Loading existing INI file: {self.config_file}")
                self.config.read(self.config_file, encoding="utf-8")
            else:
                print(
                    f"DEBUG: INI file not found, creating default: {self.config_file}"
                )
                self.save_settings()

            if not self.config.has_option("Application", "ini_location"):
                self.set("Application", "ini_location", str(self.config_file))
                self.save_settings()

            self._loaded_from_disk = True

        return self.get_all_settings()

    def reload_settings(self):
        """Force re-read settings from disk"""
        self._loaded_from_disk = False
        return self.load_settings()

    def get_all_settings(self):
        """Get all settings as a dictionary"""
        return {
            # UI settings (now in [UI] section)
            "language": self.get("UI", "language", "en"),
            "theme": self.get("UI", "theme", "system"),
            "max_height": self.getint("UI", "max_height", 600),
            "font_size": self.getint("UI", "font_size", 8),
            "ui_font_size": self.getint("UI", "ui_font_size", 9),
            # Zoom API settings
            "account_id": self.get("Zoom", "account_id", ""),
            "client_id": self.get("Zoom", "client_id", ""),
            "client_secret": self.get("Zoom", "client_secret", ""),
            "meeting_id": self.get("Zoom", "meeting_id", ""),
            # Application settings
            "debug": self.getboolean("Application", "debug", False),
            "exclude_names": self.get_exclude_names_list(),
            "poll_question": self.get("Application", "poll_question", ""),
            "ini_location": self.get(
                "Application", "ini_location", str(self.config_file)
            ),
            # Export settings (including separator)
            "csv_separator": self.get("Export", "separator", ";"),
            "export_format": self.get("Export", "format", "csv"),
            # Network settings
            "proxy": self.get("Network", "proxy", ""),
            "proxy_autodetect": self.getboolean("Network", "proxy_autodetect", True),
            # Email settings
            "smtp_server": self.get("Email", "smtp_server", ""),
            "smtp_port": self.getint("Email", "smtp_port", 587),
            "smtp_username": self.get("Email", "smtp_username", ""),
            "smtp_password": self.get("Email", "smtp_password", ""),
            "smtp_use_tls": self.getboolean("Email", "smtp_use_tls", True),
            "email_recipients": self.get_email_recipients_list(),
        }

    def save_settings(self, settings=None):
        """Save settings to INI file"""
        if settings is not None:
            # Update config with provided settings dictionary
            # UI settings go to [UI] section
            self.set("UI", "language", settings.get("language", "en"))
            self.set("UI", "theme", settings.get("theme", "system"))
            self.set("UI", "max_height", str(settings.get("max_height", 600)))
            self.set("UI", "font_size", str(settings.get("font_size", 8)))
            self.set("UI", "ui_font_size", str(settings.get("ui_font_size", 9)))

            # Zoom API settings
            self.set("Zoom", "account_id", settings.get("account_id", ""))
            self.set("Zoom", "client_id", settings.get("client_id", ""))
            self.set("Zoom", "client_secret", settings.get("client_secret", ""))
            self.set("Zoom", "meeting_id", settings.get("meeting_id", ""))

            # Application settings
            self.set("Application", "debug", str(settings.get("debug", False)))
            self.set_exclude_names_list(settings.get("exclude_names", []))
            self.set("Application", "poll_question", settings.get("poll_question", ""))
            if settings.get("ini_location"):
                self.set("Application", "ini_location", settings["ini_location"])

            # Export settings (including separator)
            self.set("Export", "separator", settings.get("csv_separator", ";"))
            self.set("Export", "format", settings.get("export_format", "csv"))

            # Network settings (preserve existing values if the caller omits them)
            self.set(
                "Network",
                "proxy",
                settings.get("proxy", self.get("Network", "proxy", "")),
            )
            self.set(
                "Network",
                "proxy_autodetect",
                str(
                    settings.get(
                        "proxy_autodetect",
                        self.getboolean("Network", "proxy_autodetect", True),
                    )
                ),
            )

            # Email settings
            self.set("Email", "smtp_server", settings.get("smtp_server", ""))
            self.set("Email", "smtp_port", str(settings.get("smtp_port", 587)))
            self.set("Email", "smtp_username", settings.get("smtp_username", ""))
            self.set("Email", "smtp_password", settings.get("smtp_password", ""))
            self.set("Email", "smtp_use_tls", str(settings.get("smtp_use_tls", True)))
            self.set_email_recipients_list(settings.get("email_recipients", []))

            # Clean up any incorrectly placed settings in UI section
            self._cleanup_misplaced_settings()

        # Ensure directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"DEBUG: Saving settings to: {self.config_file}")
        print(f"DEBUG: File exists before save: {self.config_file.exists()}")

        with open(self.config_file, "w", encoding="utf-8") as f:
            self.config.write(f)

        print(f"DEBUG: File exists after save: {self.config_file.exists()}")
        print("DEBUG: Settings saved successfully")

    def _cleanup_misplaced_settings(self):
        """Remove settings that are incorrectly placed in UI section but should be in Application section"""
        misplaced_settings = ["debug", "exclude_names", "poll_question"]

        if self.config.has_section("UI"):
            for setting in misplaced_settings:
                if self.config.has_option("UI", setting):
                    print(
                        f"DEBUG: Removing misplaced setting '{setting}' from UI section"
                    )
                    self.config.remove_option("UI", setting)

    def get(self, section, key, fallback=None):
        """Get setting value"""
        return self.config.get(section, key, fallback=fallback)

    def getboolean(self, section, key, fallback=False):
        """Get boolean setting value"""
        return self.config.getboolean(section, key, fallback=fallback)

    def getint(self, section, key, fallback=0):
        """Get integer setting value"""
        return self.config.getint(section, key, fallback=fallback)

    def set(self, section, key, value):
        """Set setting value"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def get_exclude_names_list(self) -> List[str]:
        """Get exclude names as list"""
        exclude_str = self.get("Application", "exclude_names", "")
        return [name.strip() for name in exclude_str.split(",") if name.strip()]

    def set_exclude_names_list(self, names_list: List[str]):
        """Set exclude names from list"""
        self.set("Application", "exclude_names", ",".join(names_list))

    def get_email_recipients_list(self) -> List[str]:
        """Get email recipients as list"""
        recipients_str = self.get("Email", "recipients", "")
        return [r.strip() for r in recipients_str.split(",") if r.strip()]

    def set_email_recipients_list(self, recipients_list: List[str]):
        """Set email recipients from list"""
        self.set("Email", "recipients", ",".join(recipients_list))

    def change_ini_location(self, new_path):
        """Change the location of the INI file"""
        old_config_file = self.config_file
        self.config_file = Path(new_path)

        # Save current settings to new location
        self.set("Application", "ini_location", str(self.config_file))
        self.save_settings()

        # Try to remove old file if it exists and is different
        if old_config_file.exists() and old_config_file != self.config_file:
            try:
                old_config_file.unlink()
            except Exception:
                pass  # Ignore if we can't delete the old file

    def has_api_credentials(self) -> bool:
        """Check if all required API credentials are configured"""
        required_fields = ["account_id", "client_id", "client_secret", "meeting_id"]
        return all(self.get("Zoom", field, "").strip() for field in required_fields)
