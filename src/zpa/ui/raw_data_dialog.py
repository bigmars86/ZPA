"""
Raw Data Dialog for displaying raw API responses for debugging.
"""

import json

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
)

from ..resources.translations import Translations


class RawDataDialog(QDialog):
    """Dialog to display raw API data in tabbed format for debugging"""

    def __init__(self, parent=None, raw_data=None, translations=None, font_size=8):
        super().__init__(parent)
        self.raw_data = raw_data or {}
        self.translations = translations or Translations()
        self.font_size = font_size

        # Store UI font size for use in setup_ui
        self.ui_font_size = 9  # default

        # Apply UI font to dialog
        if parent and hasattr(parent, "settings_manager"):
            settings = parent.settings_manager.load_settings()
            self.ui_font_size = settings.get("ui_font_size", 9)
            ui_font = QFont()
            ui_font.setPointSize(self.ui_font_size)
            self.setFont(ui_font)

        self.setWindowTitle("Raw API Data - Debug View")
        self.setModal(True)
        self.resize(800, 600)

        self.setup_ui()
        self.populate_data()

    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()

        # Info label
        info_label = QLabel(self.translations.get("raw_api_data_info"))
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")

        # Apply UI font to info label
        ui_font = QFont()
        ui_font.setPointSize(self.ui_font_size)
        ui_font.setBold(True)  # Keep it bold as per stylesheet
        info_label.setFont(ui_font)

        layout.addWidget(info_label)

        # Tab widget
        self.tab_widget = QTabWidget()

        # Apply UI font to tabs
        ui_font = QFont()
        ui_font.setPointSize(self.ui_font_size)
        self.tab_widget.setFont(ui_font)
        self.tab_widget.tabBar().setFont(ui_font)

        layout.addWidget(self.tab_widget)

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton(self.translations.get("close_button", "Close"))
        close_button.clicked.connect(self.close)

        # Apply UI font to close button
        ui_font = QFont()
        ui_font.setPointSize(self.ui_font_size)
        close_button.setFont(ui_font)

        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def populate_data(self):
        """Populate tabs with raw data"""
        # Meeting info tab
        if "meeting" in self.raw_data:
            meeting_text = QTextEdit()
            meeting_text.setReadOnly(True)
            meeting_text.setFont(QFont("Courier New", self.font_size))
            meeting_json = json.dumps(
                self.raw_data["meeting"], indent=2, ensure_ascii=False, default=str
            )
            meeting_text.setPlainText(meeting_json)
            self.tab_widget.addTab(
                meeting_text, self.translations.get("meeting_tab", "Meeting Data")
            )

        # Participants tab
        if "participants" in self.raw_data:
            participants_text = QTextEdit()
            participants_text.setReadOnly(True)
            participants_text.setFont(QFont("Courier New", self.font_size))
            participants_json = json.dumps(
                self.raw_data["participants"], indent=2, ensure_ascii=False, default=str
            )
            participants_text.setPlainText(participants_json)
            self.tab_widget.addTab(
                participants_text,
                self.translations.get("participants_tab", "Participants"),
            )

        # Polls tab
        if "polls" in self.raw_data:
            polls_text = QTextEdit()
            polls_text.setReadOnly(True)
            polls_text.setFont(QFont("Courier New", self.font_size))
            polls_json = json.dumps(
                self.raw_data["polls"], indent=2, ensure_ascii=False, default=str
            )
            polls_text.setPlainText(polls_json)
            self.tab_widget.addTab(
                polls_text, self.translations.get("polls_tab", "Poll Data")
            )

        # If no data available
        if not any(
            key in self.raw_data for key in ["meeting", "participants", "polls"]
        ):
            no_data_text = QTextEdit()
            no_data_text.setReadOnly(True)
            no_data_text.setPlainText("No raw API data available.")
            self.tab_widget.addTab(no_data_text, "No Data")
