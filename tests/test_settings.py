"""First-run configuration and existing configuration preservation."""

import configparser

from zpa.utils.settings_manager import SettingsManager


def test_missing_ini_is_created_with_defaults(tmp_path):
    ini_path = tmp_path / "config" / "zpa.ini"
    manager = SettingsManager(ini_path)
    config = configparser.ConfigParser()
    config.read(ini_path, encoding="utf-8")

    assert set(config.sections()) == {
        "Zoom",
        "UI",
        "Application",
        "Export",
        "Network",
        "Email",
    }
    assert all(not value for value in config["Zoom"].values())
    assert config["UI"]["language"] == "en"
    assert config["UI"]["theme"] == "system"
    assert config.getint("UI", "max_height") == 600
    assert config.getint("UI", "font_size") == 8
    assert config.getint("UI", "ui_font_size") == 9
    assert not config.getboolean("Application", "debug")
    assert config["Application"]["ini_location"] == str(ini_path)
    assert config["Export"]["format"] == "csv"
    assert config["Export"]["separator"] == ";"
    assert not config.getboolean("Network", "proxy_autodetect")
    assert config["Network"]["proxy"] == ""
    assert config.getint("Email", "smtp_port") == 587
    assert config.getboolean("Email", "smtp_use_tls")
    assert config["Email"]["smtp_password"] == ""
    assert manager.get_all_settings()["email_recipients"] == []


def test_existing_ini_is_not_overwritten(tmp_path):
    ini_path = tmp_path / "zpa.ini"
    original = "[UI]\nlanguage = de\ntheme = dark\n[Export]\nseparator = ,\n"
    ini_path.write_text(original, encoding="utf-8")

    manager = SettingsManager(ini_path)

    assert ini_path.read_text(encoding="utf-8") == original
    assert manager.get_all_settings()["language"] == "de"
    assert manager.get_all_settings()["csv_separator"] == ","
    assert manager.get_all_settings()["smtp_use_tls"] is True
