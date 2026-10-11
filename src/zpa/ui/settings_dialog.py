"""
Enhanced Settings dialog for Zoom Poll Analyzer with sections.
"""

from typing import Dict

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..resources.translations import Translations


class SettingsDialog(QDialog):
    """Enhanced settings configuration dialog with sections"""

    def __init__(
        self, parent=None, translations=None, settings_manager=None, theme_manager=None
    ):
        super().__init__(parent)
        self.translations = translations or Translations()
        self.settings_manager = settings_manager
        self.theme_manager = theme_manager

        self.setWindowTitle(self.translations.get("settings_title"))
        self.setModal(True)
        self.resize(600, 500)

        self.setup_ui()

        # Apply current UI font to settings dialog after UI setup
        if settings_manager:
            settings = settings_manager.load_settings()
            ui_font_size = settings.get("ui_font_size", 9)
            self.apply_ui_font(ui_font_size)

    def setup_ui(self):
        """Setup the dialog UI with tabs"""
        layout = QVBoxLayout()

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self.create_gui_tab()
        self.create_api_tab()
        self.create_app_tab()
        self.create_export_tab()
        self.create_email_tab()

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        # Set button texts
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(
            self.translations.get("ok_button")
        )
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(
            self.translations.get("cancel_button")
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)

    def create_gui_tab(self):
        """Create GUI settings tab"""
        tab = QWidget()
        layout = QFormLayout()

        # Language setting
        self.language_combo = QComboBox()
        for code, name in Translations.LANGUAGES.items():
            self.language_combo.addItem(name, code)
        layout.addRow(self.translations.get("language_label"), self.language_combo)

        # Theme setting
        self.theme_combo = QComboBox()
        if self.theme_manager:
            # Use dynamic themes from theme manager
            available_themes = self.theme_manager.get_available_themes()
            for code, name in available_themes.items():
                self.theme_combo.addItem(name, code)
        else:
            # Fallback to static themes
            theme_options = [
                ("light", self.translations.get("theme_light")),
                ("dark", self.translations.get("theme_dark")),
                ("system", self.translations.get("theme_system")),
            ]
            for code, name in theme_options:
                self.theme_combo.addItem(name, code)
        layout.addRow(self.translations.get("theme_label"), self.theme_combo)

        # Max height setting
        self.max_height_spin = QSpinBox()
        self.max_height_spin.setRange(400, 1200)
        self.max_height_spin.setValue(600)
        self.max_height_spin.setMinimumWidth(120)  # Match combobox width
        self.max_height_spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        layout.addRow(self.translations.get("max_height_label"), self.max_height_spin)

        # Data/Table font size setting
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 16)
        self.font_size_spin.setSingleStep(1)  # Step by 1 point
        self.font_size_spin.setValue(8)
        self.font_size_spin.setEnabled(True)  # Ensure it's enabled
        self.font_size_spin.setButtonSymbols(
            QSpinBox.ButtonSymbols.UpDownArrows
        )  # Ensure buttons are visible
        self.font_size_spin.setMinimumWidth(120)  # Match combobox width
        layout.addRow(self.translations.get("font_size_label"), self.font_size_spin)

        # UI font size setting
        self.ui_font_size_spin = QSpinBox()
        self.ui_font_size_spin.setRange(7, 18)
        self.ui_font_size_spin.setSingleStep(1)  # Step by 1 point
        self.ui_font_size_spin.setValue(9)
        self.ui_font_size_spin.setEnabled(True)
        self.ui_font_size_spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        self.ui_font_size_spin.setMinimumWidth(120)  # Match combobox width
        layout.addRow(
            self.translations.get("ui_font_size_label"), self.ui_font_size_spin
        )

        tab.setLayout(layout)
        self.tab_widget.addTab(
            tab, self.translations.get("gui_settings_tab", "GUI Settings")
        )

        # Apply minimal spinbox styling to prevent button overlap while preserving default arrows
        spinbox_style = """
        QSpinBox {
            padding-right: 20px;  /* Reserve space for buttons */
            min-height: 22px;     /* Match combobox height */
        }
        """
        self.max_height_spin.setStyleSheet(spinbox_style)
        self.font_size_spin.setStyleSheet(spinbox_style)
        self.ui_font_size_spin.setStyleSheet(spinbox_style)

    def create_api_tab(self):
        """Create API settings tab"""
        tab = QWidget()
        layout = QFormLayout()

        # API credentials
        self.account_id_edit = QLineEdit()
        self.client_id_edit = QLineEdit()
        self.client_secret_edit = QLineEdit()
        self.client_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.meeting_id_edit = QLineEdit()

        layout.addRow(self.translations.get("account_id_label"), self.account_id_edit)
        layout.addRow(self.translations.get("client_id_label"), self.client_id_edit)
        layout.addRow(
            self.translations.get("client_secret_label"), self.client_secret_edit
        )
        layout.addRow(self.translations.get("meeting_id_label"), self.meeting_id_edit)

        # Proxy / network settings
        self.proxy_autodetect_checkbox = QCheckBox()
        self.proxy_autodetect_checkbox.toggled.connect(
            self._on_proxy_autodetect_toggled
        )
        layout.addRow(
            self.translations.get("proxy_autodetect_label", "Autodetect proxy:"),
            self.proxy_autodetect_checkbox,
        )

        self.proxy_edit = QLineEdit()
        self.proxy_edit.setPlaceholderText("http://host:8080")
        layout.addRow(self.translations.get("proxy_label", "Proxy:"), self.proxy_edit)

        tab.setLayout(layout)
        self.tab_widget.addTab(
            tab, self.translations.get("api_settings_tab", "API Settings")
        )

    def _on_proxy_autodetect_toggled(self, checked):
        """Disable the manual proxy field while autodetect is enabled."""
        self.proxy_edit.setDisabled(checked)

    def create_app_tab(self):
        """Create application settings tab"""
        tab = QWidget()
        layout = QFormLayout()

        # Poll question filter
        self.poll_question_edit = QLineEdit()
        layout.addRow(
            self.translations.get("poll_question_label", "Poll Question Filter:"),
            self.poll_question_edit,
        )

        # Exclude names
        self.exclude_names_edit = QLineEdit()
        layout.addRow(
            self.translations.get("exclude_names_label"), self.exclude_names_edit
        )

        # INI file location
        ini_layout = QHBoxLayout()
        ini_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for better alignment
        ini_layout.setSpacing(6)  # Standard spacing
        self.ini_location_edit = QLineEdit()
        self.ini_location_edit.setReadOnly(True)
        ini_browse_button = QPushButton(self.translations.get("browse_button"))
        ini_browse_button.clicked.connect(self.browse_ini_location)
        ini_layout.addWidget(self.ini_location_edit)
        ini_layout.addWidget(ini_browse_button)

        ini_widget = QWidget()
        ini_widget.setContentsMargins(
            0, 0, 0, 0
        )  # Remove widget margins for better alignment
        ini_widget.setLayout(ini_layout)
        layout.addRow(self.translations.get("ini_location_label"), ini_widget)

        # Debug mode
        self.debug_checkbox = QCheckBox()
        layout.addRow(self.translations.get("debug_mode_label"), self.debug_checkbox)

        tab.setLayout(layout)
        self.tab_widget.addTab(
            tab, self.translations.get("app_settings_tab", "App Settings")
        )

    def create_export_tab(self):
        """Create export settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()

        # CSV / format settings
        form_layout = QFormLayout()
        self.csv_separator_combo = QComboBox()
        self.csv_separator_combo.addItem("; (semicolon - Excel default)", ";")
        self.csv_separator_combo.addItem(", (comma - standard CSV)", ",")
        form_layout.addRow(
            self.translations.get("csv_separator_label"), self.csv_separator_combo
        )

        self.export_format_combo = QComboBox()
        self.export_format_combo.addItem("CSV", "csv")
        self.export_format_combo.addItem("JSON", "json")
        self.export_format_combo.addItem("YAML", "yaml")
        self.export_format_combo.addItem("XML", "xml")
        form_layout.addRow(
            self.translations.get("export_format_label", "Default Export Format:"),
            self.export_format_combo,
        )
        layout.addLayout(form_layout)
        layout.addStretch()

        tab.setLayout(layout)
        self.tab_widget.addTab(
            tab, self.translations.get("export_settings_tab", "Export Settings")
        )

    def create_email_tab(self):
        """Create email settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()

        # SMTP Settings group
        smtp_group = QGroupBox(
            self.translations.get("smtp_settings_group", "SMTP Settings")
        )
        smtp_form = QFormLayout()

        self.smtp_server_edit = QLineEdit()
        smtp_form.addRow(
            self.translations.get("smtp_server_label", "SMTP Server:"),
            self.smtp_server_edit,
        )

        self.smtp_port_spin = QSpinBox()
        self.smtp_port_spin.setRange(1, 65535)
        self.smtp_port_spin.setValue(587)
        self.smtp_port_spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        smtp_form.addRow(
            self.translations.get("smtp_port_label", "SMTP Port:"), self.smtp_port_spin
        )

        self.smtp_username_edit = QLineEdit()
        smtp_form.addRow(
            self.translations.get("smtp_username_label", "Username / Sender:"),
            self.smtp_username_edit,
        )

        self.smtp_password_edit = QLineEdit()
        self.smtp_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        smtp_form.addRow(
            self.translations.get("smtp_password_label", "Password:"),
            self.smtp_password_edit,
        )

        self.smtp_use_tls_checkbox = QCheckBox()
        self.smtp_use_tls_checkbox.setChecked(True)
        smtp_form.addRow(
            self.translations.get("smtp_use_tls_label", "Use TLS:"),
            self.smtp_use_tls_checkbox,
        )

        smtp_group.setLayout(smtp_form)
        layout.addWidget(smtp_group)

        # Email Recipients group
        recipients_group = QGroupBox(
            self.translations.get("email_recipients_group", "Email Recipients")
        )
        recipients_layout = QVBoxLayout()

        self.recipients_scroll = QScrollArea()
        self.recipients_scroll.setWidgetResizable(True)
        self.recipients_scroll.setFixedHeight(120)

        self.recipients_container = QWidget()
        self.recipients_inner_layout = QVBoxLayout(self.recipients_container)
        self.recipients_inner_layout.setContentsMargins(2, 2, 2, 2)
        self.recipients_inner_layout.setSpacing(4)
        self.recipients_inner_layout.addStretch()

        self.recipients_scroll.setWidget(self.recipients_container)
        recipients_layout.addWidget(self.recipients_scroll)

        add_btn = QPushButton(self.translations.get("add_email_button", "+ Add Email"))
        add_btn.clicked.connect(lambda: self.add_email_recipient())
        recipients_layout.addWidget(add_btn)

        self.email_recipient_rows = []  # list of (row_widget, QLineEdit) tuples

        recipients_group.setLayout(recipients_layout)
        layout.addWidget(recipients_group)
        layout.addStretch()

        tab.setLayout(layout)
        self.tab_widget.addTab(
            tab, self.translations.get("email_settings_tab", "Email Settings")
        )

    def add_email_recipient(self, email=""):
        """Add a new email recipient row"""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        edit = QLineEdit()
        edit.setPlaceholderText(
            self.translations.get("email_placeholder", "email@example.com")
        )
        if email:
            edit.setText(email)
        row_layout.addWidget(edit)

        remove_btn = QPushButton("✕")
        remove_btn.setFixedWidth(28)
        remove_btn.setToolTip(self.translations.get("remove_email_tooltip", "Remove"))
        remove_btn.clicked.connect(lambda: self.remove_email_recipient(row_widget))
        row_layout.addWidget(remove_btn)

        # Insert before the trailing stretch
        stretch_index = self.recipients_inner_layout.count() - 1
        self.recipients_inner_layout.insertWidget(stretch_index, row_widget)
        self.email_recipient_rows.append((row_widget, edit))

    def remove_email_recipient(self, row_widget):
        """Remove an email recipient row"""
        self.email_recipient_rows = [
            (w, e) for w, e in self.email_recipient_rows if w is not row_widget
        ]
        row_widget.setParent(None)
        row_widget.deleteLater()

    def browse_ini_location(self):
        """Browse for INI file location"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.translations.get("ini_file_dialog"),
            self.ini_location_edit.text() or "zoom_poll_analyzer.ini",
            self.translations.get("ini_filter"),
        )

        if filename:
            self.ini_location_edit.setText(filename)

    def get_settings(self) -> Dict:
        """Get current settings from the dialog"""
        exclude_names = [
            name.strip()
            for name in self.exclude_names_edit.text().split(",")
            if name.strip()
        ]
        return {
            # GUI settings
            "language": self.language_combo.currentData(),
            "theme": self.theme_combo.currentData(),
            "max_height": self.max_height_spin.value(),
            "font_size": self.font_size_spin.value(),
            "ui_font_size": self.ui_font_size_spin.value(),
            # API settings
            "account_id": self.account_id_edit.text(),
            "client_id": self.client_id_edit.text(),
            "client_secret": self.client_secret_edit.text(),
            "meeting_id": self.meeting_id_edit.text(),
            "proxy": self.proxy_edit.text().strip(),
            "proxy_autodetect": self.proxy_autodetect_checkbox.isChecked(),
            # App settings
            "poll_question": self.poll_question_edit.text(),
            "exclude_names": exclude_names,
            "ini_location": self.ini_location_edit.text(),
            "debug": self.debug_checkbox.isChecked(),
            # Export settings
            "csv_separator": self.csv_separator_combo.currentData(),
            "export_format": self.export_format_combo.currentData(),
            # Email settings
            "smtp_server": self.smtp_server_edit.text(),
            "smtp_port": self.smtp_port_spin.value(),
            "smtp_username": self.smtp_username_edit.text(),
            "smtp_password": self.smtp_password_edit.text(),
            "smtp_use_tls": self.smtp_use_tls_checkbox.isChecked(),
            "email_recipients": [
                edit.text().strip()
                for _, edit in self.email_recipient_rows
                if edit.text().strip()
            ],
        }

    def set_settings(self, settings: Dict):
        """Set dialog values from settings"""
        # GUI settings
        language = settings.get("language", "en")
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == language:
                self.language_combo.setCurrentIndex(i)
                break

        theme = settings.get("theme", "system")
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == theme:
                self.theme_combo.setCurrentIndex(i)
                break

        self.max_height_spin.setValue(settings.get("max_height", 600))
        self.font_size_spin.setValue(settings.get("font_size", 8))
        self.ui_font_size_spin.setValue(settings.get("ui_font_size", 9))

        # API settings
        self.account_id_edit.setText(settings.get("account_id", ""))
        self.client_id_edit.setText(settings.get("client_id", ""))
        self.client_secret_edit.setText(settings.get("client_secret", ""))
        self.meeting_id_edit.setText(settings.get("meeting_id", ""))
        autodetect = settings.get("proxy_autodetect", False)
        self.proxy_autodetect_checkbox.setChecked(autodetect)
        self.proxy_edit.setText(settings.get("proxy", ""))
        self.proxy_edit.setDisabled(autodetect)

        # App settings
        self.poll_question_edit.setText(settings.get("poll_question", ""))
        self.exclude_names_edit.setText(", ".join(settings.get("exclude_names", [])))
        self.ini_location_edit.setText(settings.get("ini_location", ""))
        self.debug_checkbox.setChecked(settings.get("debug", False))

        # Export settings
        csv_sep = settings.get("csv_separator", ";")
        for i in range(self.csv_separator_combo.count()):
            if self.csv_separator_combo.itemData(i) == csv_sep:
                self.csv_separator_combo.setCurrentIndex(i)
                break

        export_format = settings.get("export_format", "csv")
        for i in range(self.export_format_combo.count()):
            if self.export_format_combo.itemData(i) == export_format:
                self.export_format_combo.setCurrentIndex(i)

        # Email settings
        self.smtp_server_edit.setText(settings.get("smtp_server", ""))
        self.smtp_port_spin.setValue(settings.get("smtp_port", 587))
        self.smtp_username_edit.setText(settings.get("smtp_username", ""))
        self.smtp_password_edit.setText(settings.get("smtp_password", ""))
        self.smtp_use_tls_checkbox.setChecked(settings.get("smtp_use_tls", True))

        # Clear existing recipient rows and repopulate
        for row_widget, _ in self.email_recipient_rows:
            row_widget.setParent(None)
            row_widget.deleteLater()
        self.email_recipient_rows = []
        for email in settings.get("email_recipients", []):
            self.add_email_recipient(email)

    def apply_ui_font(self, font_size):
        """Apply UI font to all dialog widgets"""
        font = QFont()
        font.setPointSize(font_size)

        # Apply to dialog itself
        self.setFont(font)

        # Apply to tab widget and tabs
        if hasattr(self, "tab_widget"):
            self.tab_widget.setFont(font)
            self.tab_widget.tabBar().setFont(font)

            # Apply to all tab contents
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if widget:
                    widget.setFont(font)

        # Apply to all buttons
        for button in self.findChildren(QPushButton):
            current_style = button.styleSheet()
            button.setStyleSheet("")  # Temporarily clear stylesheet
            button.setFont(font)
            button.setStyleSheet(current_style)  # Restore stylesheet
            button.updateGeometry()
            button.update()

        # Apply to all labels
        for label in self.findChildren(QLabel):
            label.setFont(font)

        # Apply to all input widgets
        for widget in self.findChildren((QLineEdit, QSpinBox, QComboBox, QCheckBox)):
            widget.setFont(font)

        # Apply to button box
        for button_box in self.findChildren(QDialogButtonBox):
            button_box.setFont(font)
            # Apply to individual buttons in the button box
            for button in button_box.buttons():
                button.setFont(font)
