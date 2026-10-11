"""
ZPA (Zoom Poll Analyzer) - Main GUI Application
"""

import argparse
import json
import smtplib
import sys
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# PyInstaller compatibility: adjust path when running as executable
if getattr(sys, "frozen", False):
    # Running as PyInstaller executable
    bundle_dir = Path(sys._MEIPASS)
    sys.path.insert(0, str(bundle_dir))

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

# Conditional imports: handle both development and PyInstaller environments
try:
    # First, try absolute imports (works for PyInstaller and some development setups)
    from zpa import __version__
    from zpa.core.data_processor import parse_iso_datetime
    from zpa.core.export_manager import ExportManager
    from zpa.core.zoom_api import ZoomAPI, resolve_proxy, test_internet
    from zpa.resources.translations import Translations
    from zpa.ui.components.status_led import StatusLED
    from zpa.ui.past_meetings_dialog import PastMeetingsDialog
    from zpa.ui.poll_table import PollTableContainer
    from zpa.ui.raw_data_dialog import RawDataDialog
    from zpa.ui.settings_dialog import SettingsDialog
    from zpa.utils.resource_paths import get_icons_dir
    from zpa.utils.settings_manager import SettingsManager
    from zpa.utils.theme_manager import ThemeManager
except ImportError:
    # Fallback to relative imports (for development when running as module)
    try:
        from . import __version__
        from .core.data_processor import parse_iso_datetime
        from .core.export_manager import ExportManager
        from .core.zoom_api import ZoomAPI, resolve_proxy, test_internet
        from .resources.translations import Translations
        from .ui.components.status_led import StatusLED
        from .ui.past_meetings_dialog import PastMeetingsDialog
        from .ui.poll_table import PollTableContainer
        from .ui.raw_data_dialog import RawDataDialog
        from .ui.settings_dialog import SettingsDialog
        from .utils.resource_paths import get_icons_dir
        from .utils.settings_manager import SettingsManager
        from .utils.theme_manager import ThemeManager
    except ImportError as e:
        print(f"Failed to import required modules: {e}")
        print(f"Python path: {sys.path}")
        if hasattr(sys, "_MEIPASS"):
            print(f"PyInstaller temp directory: {sys._MEIPASS}")
        sys.exit(1)


# UI Constants
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
STATUS_BAR_HEIGHT = 24
TOOLBAR_HEIGHT = 50
PROGRESS_BAR_HEIGHT = 10
WINDOW_MARGINS_PADDING = 40
RESIZE_THRESHOLD = 20
MIN_TABLE_HEIGHT = 600
MAX_TABLE_HEIGHT = 1000


class DataLoadWorker(QThread):
    """Worker thread for loading data from Zoom API"""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, zoom_api, meeting_id, debug=False, meeting_uuid=None):
        super().__init__()
        self.zoom_api = zoom_api
        self.meeting_id = meeting_id
        self.meeting_uuid = meeting_uuid
        self.debug = debug

    def run(self):
        try:
            if self.debug:
                print(f"Debug: Starting data load for meeting ID: {self.meeting_id}")

            self.progress.emit("Connecting to Zoom API...")

            # A specific past instance is addressed by its (encoded) UUID; the
            # latest instance is addressed by the numeric meeting id.
            ref = (
                self.zoom_api.encode_uuid(self.meeting_uuid)
                if self.meeting_uuid
                else self.meeting_id
            )

            # Get meeting info first
            meeting_data = self.zoom_api.get_meeting_info(ref, debug=self.debug)

            if self.debug:
                print("Debug: Meeting data structure:")
                print(json.dumps(meeting_data, indent=2, default=str))

            self.progress.emit("Processing meeting data...")

            # Get participants
            participants = self.zoom_api.get_participants(ref)

            if self.debug:
                print(f"Debug: Found {len(participants)} participants")

            self.progress.emit("Getting poll data...")

            # Get polls using the correct method
            try:
                polls_data = self.zoom_api.get_poll_results(ref, debug=self.debug)
                # Extract questions (which contain the poll responses)
                polls = polls_data.get("questions", []) if polls_data else []

                if self.debug:
                    print(
                        f"Debug: Extracted {len(polls)} poll responses from API response"
                    )

            except Exception as poll_error:
                if self.debug:
                    print(f"Debug: Error getting polls: {poll_error}")
                polls = []

            if self.debug:
                print(f"Debug: Found {len(polls)} polls")
                for i, poll in enumerate(polls):
                    print(f"Debug: Poll {i + 1}: {poll.get('title', 'No title')}")

            result = {
                "meeting": meeting_data,
                "participants": participants,
                "polls": polls,
            }

            self.finished.emit(result)

        except Exception as e:
            error_msg = str(e)
            if self.debug:
                print(f"Debug: Error in DataLoadWorker: {error_msg}")
                error_msg += f"\n\nFull traceback:\n{traceback.format_exc()}"
                print(f"Debug: Full traceback:\n{traceback.format_exc()}")
            self.error.emit(error_msg)


class ConnectionTestWorker(QThread):
    """Background worker that checks internet / Zoom reachability."""

    result = pyqtSignal(bool)

    def __init__(self, proxy=None):
        super().__init__()
        self.proxy = proxy

    def run(self):
        try:
            ok = test_internet(self.proxy)
        except Exception:
            ok = False
        self.result.emit(ok)


class ZoomPollAnalyzer(QMainWindow):
    """Main application window"""

    def __init__(self, ini_file_path=None):
        super().__init__()

        # Initialize core components
        self.settings_manager = SettingsManager(ini_file_path)
        self.translations = Translations()
        self.theme_manager = None  # Will be initialized after QApplication is available

        # Load settings
        settings = self.settings_manager.load_settings()
        debug_mode = settings.get("debug", False)

        if debug_mode:
            print("Debug: Initializing ZPA (Zoom Poll Analyzer)")
            print(f"Debug: Loaded settings: {settings}")

        # Apply language
        language = settings.get("language", "en")
        if debug_mode:
            print(f"Debug: Setting language to: {language}")
        self.translations.set_language(language)

        # Initialize theme manager now that we have QApplication
        app = QApplication.instance()
        self.theme_manager = ThemeManager(app)

        # Apply theme
        theme = settings.get("theme", "system")
        if debug_mode:
            print(f"Debug: Applying theme: {theme}")
        self.theme_manager.apply_theme(theme)

        # Ensure consistent layout after theme application
        self.ensure_consistent_layout()

        # Initialize API and export manager
        self.zoom_api = None
        self.export_manager = ExportManager()

        # Data storage
        self.current_data = None
        self.current_meeting_uuid = None  # UUID of loaded past instance (None = latest)
        self.active_proxy = None  # Effective proxy in use (None = direct connection)
        self.conn_worker = None  # Background connectivity-test thread
        self.processed_data = []
        self.raw_api_data = None  # Store raw API data for debugging

        # Email state
        self.email_sent = False

        # Worker thread
        self.worker = None

        # Initialize UI
        self.init_ui()

        # Load API credentials if available
        self.load_api_credentials()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Zoom Poll Analyzer")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # Position window 10% from top of screen
        self.position_window_startup()

        # Set window icon
        icon_path = get_icons_dir() / "zoom-icon.ico"
        print(f"DEBUG: Looking for icon at: {icon_path}")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            print(f"DEBUG: Icon loaded successfully from: {icon_path}")
        else:
            print(f"DEBUG: Icon not found at: {icon_path}")

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Create menu bar
        self.create_menu_bar()

        # Create toolbar
        self.create_toolbar(layout)

        # Create main content area
        self.create_content_area(layout)

        # Create status bar
        self.create_status_bar()

        # Update UI text
        self.update_ui_text()

        # Apply UI font after all UI elements are created
        settings = self.settings_manager.load_settings()
        self.update_ui_font(settings.get("ui_font_size", 9))
        self.setup_status_bar_font()  # Use standard 8px font for status bar

    def create_menu_bar(self):
        """Create application menu bar"""
        self.menubar = self.menuBar()

        # File menu
        self.file_menu = self.menubar.addMenu("File")

        # Settings action
        self.settings_action = QAction("Settings", self)
        self.settings_action.setShortcut("Ctrl+S")
        self.settings_action.triggered.connect(self.show_settings)
        self.file_menu.addAction(self.settings_action)

        # Past meeting action
        self.past_meetings_action = QAction("Past Meeting\u2026", self)
        self.past_meetings_action.triggered.connect(self.show_past_meetings)
        self.file_menu.addAction(self.past_meetings_action)

        self.file_menu.addSeparator()

        # Export submenu
        self.export_menu = self.file_menu.addMenu("Export")

        self.export_csv_action = QAction(self.translations.get("export_csv"), self)
        self.export_csv_action.setShortcut("Ctrl+E")
        self.export_csv_action.triggered.connect(lambda: self.export_data("csv"))
        self.export_csv_action.setEnabled(False)
        self.export_menu.addAction(self.export_csv_action)

        self.export_json_action = QAction(self.translations.get("export_json"), self)
        self.export_json_action.setShortcut("Ctrl+J")
        self.export_json_action.triggered.connect(lambda: self.export_data("json"))
        self.export_json_action.setEnabled(False)
        self.export_menu.addAction(self.export_json_action)

        self.export_yaml_action = QAction(self.translations.get("export_yaml"), self)
        self.export_yaml_action.setShortcut("Ctrl+Y")
        self.export_yaml_action.triggered.connect(lambda: self.export_data("yaml"))
        self.export_yaml_action.setEnabled(False)
        self.export_menu.addAction(self.export_yaml_action)

        self.export_xml_action = QAction(self.translations.get("export_xml"), self)
        self.export_xml_action.setShortcut("Ctrl+X")
        self.export_xml_action.triggered.connect(lambda: self.export_data("xml"))
        self.export_xml_action.setEnabled(False)
        self.export_menu.addAction(self.export_xml_action)

        self.file_menu.addSeparator()

        # Exit action
        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        # View menu
        self.view_menu = self.menubar.addMenu("View")

        # Theme submenu
        self.theme_menu = self.view_menu.addMenu("Theme")
        self.theme_actions = {}  # Store theme actions for later updates

        # Populate theme menu dynamically
        self.populate_theme_menu()

        # Language submenu
        self.language_menu = self.view_menu.addMenu("Language")

        self.english_action = QAction("English", self)
        self.english_action.triggered.connect(lambda: self.change_language("en"))
        self.language_menu.addAction(self.english_action)

        self.german_action = QAction("Deutsch", self)
        self.german_action.triggered.connect(lambda: self.change_language("de"))
        self.language_menu.addAction(self.german_action)

        self.greek_action = QAction("Ελληνικά", self)
        self.greek_action.triggered.connect(lambda: self.change_language("el"))
        self.language_menu.addAction(self.greek_action)

        # Debug menu
        self.debug_menu = self.menubar.addMenu(self.translations.get("menu_debug"))

        self.view_raw_data_action = QAction(
            self.translations.get("view_raw_data"), self
        )
        self.view_raw_data_action.triggered.connect(self.view_raw_data)
        self.view_raw_data_action.setEnabled(False)  # Enabled after data is loaded
        self.debug_menu.addAction(self.view_raw_data_action)

        # Help menu
        self.help_menu = self.menubar.addMenu("Help")

        self.about_action = QAction("About", self)
        self.about_action.triggered.connect(self.show_about)
        self.help_menu.addAction(self.about_action)

    def create_toolbar(self, layout):
        """Create toolbar with main controls"""
        toolbar_layout = QHBoxLayout()

        # Load data button
        self.load_button = QPushButton()
        self.load_button.clicked.connect(self.load_data)
        toolbar_layout.addWidget(self.load_button)

        # Past meeting button
        self.past_button = QPushButton()
        self.past_button.clicked.connect(self.show_past_meetings)
        toolbar_layout.addWidget(self.past_button)

        # Refresh button
        self.refresh_button = QPushButton()
        self.refresh_button.clicked.connect(self.refresh_data)
        self.refresh_button.setEnabled(False)
        toolbar_layout.addWidget(self.refresh_button)

        # Export button
        self.export_button = QPushButton()
        self.export_button.clicked.connect(
            lambda: self.export_data()
        )  # Use default format from settings
        self.export_button.setEnabled(False)
        toolbar_layout.addWidget(self.export_button)

        # Send button
        self.send_button = QPushButton()
        self.send_button.clicked.connect(self.send_email)
        self.send_button.setEnabled(False)
        toolbar_layout.addWidget(self.send_button)

        toolbar_layout.addStretch()

        # Settings button
        self.settings_button = QPushButton()
        self.settings_button.clicked.connect(self.show_settings)
        toolbar_layout.addWidget(self.settings_button)

        layout.addLayout(toolbar_layout)

    def create_content_area(self, layout):
        """Create main content area"""
        # Thin progress bar (like a line)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(3)  # Very thin line
        self.progress_bar.setTextVisible(False)  # No text on such a thin bar
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #e0e0e0;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 1px;
            }
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Create splitter for data tables
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Poll results table container (includes main table + total row)
        self.table = PollTableContainer()

        # Apply table font from settings (others will be applied after full UI creation)
        settings = self.settings_manager.load_settings()
        self.update_table_font(settings.get("font_size", 8))

        splitter.addWidget(self.table)

        # Set splitter proportions
        splitter.setSizes([800])

        layout.addWidget(splitter, 1)  # Give it stretch factor

    def populate_theme_menu(self):
        """Populate theme menu with available themes"""
        if not self.theme_manager:
            return

        # Clear existing actions
        self.theme_menu.clear()
        self.theme_actions.clear()

        # Get available themes
        available_themes = self.theme_manager.get_available_themes()

        # Create actions for each theme
        for theme_key, theme_name in available_themes.items():
            action = QAction(theme_name, self)
            action.triggered.connect(
                lambda checked, key=theme_key: self.change_theme(key)
            )
            self.theme_menu.addAction(action)
            self.theme_actions[theme_key] = action

    def create_status_bar(self):
        """Create ultra-compact status bar with status LEDs"""
        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(
            False
        )  # Remove resize grip that interferes with right positioning
        self.status_bar.setStyleSheet("""
            QStatusBar {
                padding: 0px;
                margin: 0px;
                border: none;
            }
        """)  # Removed hardcoded height to allow scaling with font size
        self.status_bar.setContentsMargins(0, 0, 0, 0)
        self.setStatusBar(self.status_bar)

        # Create left widget for main status info
        left_widget = QWidget()
        left_widget.setContentsMargins(0, 0, 0, 0)  # No margins on widget
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 2, 5, 2)  # Consistent 5px left/right padding
        left_layout.setSpacing(0)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.status_info = QLabel()
        self.status_info.setStyleSheet("""
            padding: 0px;
            margin: 0px;
            line-height: 1;
        """)
        self.status_info.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        left_layout.addWidget(self.status_info)

        # Add left widget to status bar
        self.status_bar.addWidget(left_widget)

        # Add stretch to push LEDs to the right
        spacer_widget = QWidget()
        self.status_bar.addWidget(spacer_widget, 1)  # Stretch factor of 1

        # Create right widget for status LEDs
        right_widget = QWidget()
        right_widget.setContentsMargins(0, 0, 0, 0)  # No margins on widget
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 2, 5, 2)  # Consistent 5px left/right padding
        right_layout.setSpacing(0)  # No spacing between elements
        right_layout.setAlignment(
            Qt.AlignmentFlag.AlignVCenter
        )  # Center all content vertically
        # INI File status
        ini_layout = QHBoxLayout()
        ini_layout.setContentsMargins(0, 0, 0, 0)  # No layout margins
        ini_layout.setSpacing(0)  # No spacing in layout
        ini_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Center vertically
        self.ini_status_led = StatusLED()
        self.ini_label = QLabel("INI")
        self.ini_label.setStyleSheet("margin-left: 2px; padding: 0px; line-height: 1;")
        ini_layout.addWidget(self.ini_status_led)
        ini_layout.addWidget(self.ini_label)

        ini_widget = QWidget()
        ini_widget.setContentsMargins(
            0, 0, 0, 0
        )  # No extra margins - padding handled by parent
        ini_widget.setLayout(ini_layout)
        right_layout.addWidget(ini_widget)

        # Add small spacer between INI and API
        spacer = QSpacerItem(4, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        right_layout.addItem(spacer)

        # API status
        api_layout = QHBoxLayout()
        api_layout.setContentsMargins(0, 0, 0, 0)  # No layout margins
        api_layout.setSpacing(0)  # No spacing in layout
        api_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Center vertically
        self.api_status_led = StatusLED()
        self.api_label = QLabel("API")
        self.api_label.setStyleSheet("margin-left: 2px; padding: 0px; line-height: 1;")
        api_layout.addWidget(self.api_status_led)
        api_layout.addWidget(self.api_label)

        api_widget = QWidget()
        api_widget.setContentsMargins(
            0, 0, 0, 0
        )  # No extra margins - padding handled by parent
        api_widget.setLayout(api_layout)
        right_layout.addWidget(api_widget)

        # Add small spacer between API and Proxy
        right_layout.addItem(
            QSpacerItem(4, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        )

        # Proxy status (green when a proxy is in use)
        proxy_layout = QHBoxLayout()
        proxy_layout.setContentsMargins(0, 0, 0, 0)
        proxy_layout.setSpacing(0)
        proxy_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.proxy_status_led = StatusLED()
        self.proxy_label = QLabel("Proxy")
        self.proxy_label.setStyleSheet(
            "margin-left: 2px; padding: 0px; line-height: 1;"
        )
        proxy_layout.addWidget(self.proxy_status_led)
        proxy_layout.addWidget(self.proxy_label)
        proxy_widget = QWidget()
        proxy_widget.setContentsMargins(0, 0, 0, 0)
        proxy_widget.setLayout(proxy_layout)
        right_layout.addWidget(proxy_widget)

        # Add small spacer between Proxy and Conn
        right_layout.addItem(
            QSpacerItem(4, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        )

        # Connection status (green when the internet/Zoom test succeeds)
        conn_layout = QHBoxLayout()
        conn_layout.setContentsMargins(0, 0, 0, 0)
        conn_layout.setSpacing(0)
        conn_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.conn_status_led = StatusLED()
        self.conn_label = QLabel("Conn")
        self.conn_label.setStyleSheet("margin-left: 2px; padding: 0px; line-height: 1;")
        conn_layout.addWidget(self.conn_status_led)
        conn_layout.addWidget(self.conn_label)
        conn_widget = QWidget()
        conn_widget.setContentsMargins(0, 0, 0, 0)
        conn_widget.setLayout(conn_layout)
        right_layout.addWidget(conn_widget)

        self.status_bar.addWidget(right_widget)

        # Initialize status
        self.update_status_indicators()

        # Apply standard font and styling after all elements are created
        self.setup_status_bar_font()

    def ensure_consistent_layout(self):
        """Ensure consistent layout regardless of theme"""
        # Ensure LED consistency only (status bar height is managed by font settings)
        if hasattr(self, "ini_status_led"):
            self.ini_status_led.setFixedSize(8, 8)
        if hasattr(self, "api_status_led"):
            self.api_status_led.setFixedSize(8, 8)
        if hasattr(self, "proxy_status_led"):
            self.proxy_status_led.setFixedSize(8, 8)
        if hasattr(self, "conn_status_led"):
            self.conn_status_led.setFixedSize(8, 8)

    def position_window_startup(self):
        """Position window approximately 10% from the top of the monitor on startup"""
        try:
            # Get the primary screen
            app = QApplication.instance()
            if app:
                screen = app.primaryScreen()
                if screen:
                    # Get screen geometry (available area excluding taskbars etc.)
                    screen_geometry = screen.availableGeometry()

                    # Calculate window size (use default size if not set)
                    window_width = 800  # Default width
                    window_height = 600  # Default height

                    # Calculate position: 10% from top, centered horizontally
                    x = (
                        screen_geometry.width() - window_width
                    ) // 2 + screen_geometry.x()
                    y = int(screen_geometry.height() * 0.1) + screen_geometry.y()

                    # Set window size and position
                    self.resize(window_width, window_height)
                    self.move(x, y)

                    print(
                        f"DEBUG: Positioned window at ({x}, {y}) with size ({window_width}, {window_height})"
                    )
                    print(
                        f"DEBUG: Screen geometry: {screen_geometry.width()}x{screen_geometry.height()}"
                    )
        except Exception as e:
            print(f"DEBUG: Failed to position window: {e}")
            # Fall back to default positioning
            pass

    def update_status_indicators(self):
        """Update INI and API status LEDs and ready status"""
        settings = self.settings_manager.load_settings()

        # Update INI status (always green if we got here, since we loaded settings)
        self.ini_status_led.set_status("ok")

        # Update API status
        account_id = settings.get("account_id", "")
        client_id = settings.get("client_id", "")
        client_secret = settings.get("client_secret", "")

        if account_id and client_id and client_secret:
            self.api_status_led.set_status("ok")
            if not hasattr(self, "current_data") or not self.current_data:
                self.status_info.setText("Ready")
        else:
            self.api_status_led.set_status("error")
            if not hasattr(self, "current_data") or not self.current_data:
                self.status_info.setText("Not Ready")

        # Proxy LED: green when a proxy is in use, gray for a direct connection
        if hasattr(self, "proxy_status_led"):
            self.proxy_status_led.set_status(
                "ok" if getattr(self, "active_proxy", None) else "unknown"
            )

    def _start_connection_test(self):
        """Run a background connectivity check and update the Conn LED."""
        if hasattr(self, "conn_status_led"):
            self.conn_status_led.set_status("unknown")  # testing in progress
        if self.conn_worker is not None and self.conn_worker.isRunning():
            return
        self.conn_worker = ConnectionTestWorker(getattr(self, "active_proxy", None))
        self.conn_worker.result.connect(self._on_connection_tested)
        self.conn_worker.finished.connect(self.conn_worker.deleteLater)
        self.conn_worker.start()

    def _on_connection_tested(self, ok):
        """Apply the background connection-test result to the Conn LED."""
        if hasattr(self, "conn_status_led"):
            self.conn_status_led.set_status("ok" if ok else "error")
        self.conn_worker = None

    def update_ui_text(self):
        """Update all UI text with current language"""
        # Debug translation loading
        settings = self.settings_manager.load_settings()
        debug_mode = settings.get("debug", False)

        if debug_mode:
            print(
                f"Debug: Updating UI text with language: {self.translations.current_language}"
            )
            print(
                f"Debug: Sample translation test - app_title: '{self.translations.get('app_title')}'"
            )

        # Window title
        self.setWindowTitle(self.translations.get("app_title"))

        # Menu bar
        self.file_menu.setTitle(self.translations.get("menu_file"))
        self.settings_action.setText(self.translations.get("menu_settings"))
        self.past_meetings_action.setText(self.translations.get("menu_past_meeting"))
        self.export_menu.setTitle(self.translations.get("export_menu"))
        self.export_csv_action.setText(self.translations.get("export_csv"))
        self.export_json_action.setText(self.translations.get("export_json"))
        self.export_yaml_action.setText(self.translations.get("export_yaml"))
        self.export_xml_action.setText(self.translations.get("export_xml"))
        self.exit_action.setText(self.translations.get("menu_exit"))

        self.view_menu.setTitle(self.translations.get("menu_view"))
        self.theme_menu.setTitle(self.translations.get("menu_theme"))

        # Update theme action texts if using static translations
        # Note: Dynamic themes from JSON use their own names
        if "light" in self.theme_actions:
            self.theme_actions["light"].setText(self.translations.get("theme_light"))
        if "dark" in self.theme_actions:
            self.theme_actions["dark"].setText(self.translations.get("theme_dark"))
        if "system" in self.theme_actions:
            self.theme_actions["system"].setText(self.translations.get("theme_system"))

        self.language_menu.setTitle(self.translations.get("menu_language"))
        self.english_action.setText("English")
        self.german_action.setText("Deutsch")
        self.greek_action.setText("Ελληνικά")

        self.help_menu.setTitle(self.translations.get("menu_help"))
        self.about_action.setText(self.translations.get("menu_about"))

        self.debug_menu.setTitle(self.translations.get("menu_debug"))
        self.view_raw_data_action.setText(self.translations.get("view_raw_data"))

        # Buttons
        self.load_button.setText(self.translations.get("load_data_button"))
        self.past_button.setText(self.translations.get("past_meeting_button"))
        self.refresh_button.setText(self.translations.get("refresh_button"))
        self.export_button.setText(self.translations.get("export_button"))
        self.send_button.setText(self.translations.get("send_button"))
        self.settings_button.setText(self.translations.get("settings_button"))

        # Status
        if hasattr(self, "current_data") and self.current_data:
            self.update_status_info()
        else:
            self.status_label.setText(self.translations.get("status_ready"))

    def load_api_credentials(self):
        """Load API credentials from settings"""
        settings = self.settings_manager.load_settings()

        account_id = settings.get("account_id", "")
        client_id = settings.get("client_id", "")
        client_secret = settings.get("client_secret", "")

        # Resolve the effective proxy (system autodetect or manual value)
        self.active_proxy = resolve_proxy(
            settings.get("proxy_autodetect", False), settings.get("proxy", "")
        )

        if account_id and client_id and client_secret:
            self.zoom_api = ZoomAPI(
                account_id, client_id, client_secret, proxy=self.active_proxy
            )

        # Reflect proxy state and (re)check connectivity in the status LEDs
        self.update_status_indicators()
        self._start_connection_test()

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(
            self, self.translations, self.settings_manager, self.theme_manager
        )

        # Load current settings
        current_settings = self.settings_manager.load_settings()
        dialog.set_settings(current_settings)

        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            # Get new settings
            new_settings = dialog.get_settings()

            # Save settings
            self.settings_manager.save_settings(new_settings)

            # Apply language change
            if new_settings.get("language") != current_settings.get("language"):
                self.change_language(new_settings.get("language"))

            # Apply theme change
            if new_settings.get("theme") != current_settings.get("theme"):
                self.change_theme(new_settings.get("theme"))

            # Reload API credentials
            self.load_api_credentials()

            # Update status indicators
            self.update_status_indicators()

            # Update font sizes if changed
            if new_settings.get("font_size") != current_settings.get("font_size"):
                self.update_table_font(new_settings.get("font_size"))
            if new_settings.get("ui_font_size") != current_settings.get("ui_font_size"):
                self.update_ui_font(new_settings.get("ui_font_size"))
            # Status bar font is now fixed at 8px - no need to update

    def change_language(self, language_code):
        """Change application language"""
        self.translations.set_language(language_code)
        self.update_ui_text()

        # Save language preference
        settings = self.settings_manager.load_settings()
        settings["language"] = language_code
        self.settings_manager.save_settings(settings)

        # Update table with new translations if data exists
        if hasattr(self, "processed_data") and self.processed_data:
            settings = self.settings_manager.load_settings()
            debug_mode = settings.get("debug", False)
            exclude_names = settings.get("exclude_names", [])
            theme_colors = (
                self.theme_manager.get_current_theme_colors()
                if self.theme_manager
                else {}
            )
            self.table.populate_data(
                self.processed_data,
                self.translations,
                debug_mode,
                exclude_names,
                theme_colors,
            )
            # Reapply table font after populate_data (stylesheet might override font)
            self.update_table_font(settings.get("font_size", 8))

    def change_theme(self, theme_name):
        """Change application theme"""
        self.theme_manager.apply_theme(theme_name)

        # Ensure consistent layout after theme change
        self.ensure_consistent_layout()

        # Reapply font settings after theme change (themes might override fonts)
        settings = self.settings_manager.load_settings()
        self.update_ui_font(settings.get("ui_font_size", 9))
        self.setup_status_bar_font()  # Restore standard 8px status bar font
        self.update_table_font(settings.get("font_size", 8))

        # Refresh table colors after theme change
        if hasattr(self, "processed_data") and self.processed_data:
            debug_mode = settings.get("debug", False)
            exclude_names = settings.get("exclude_names", [])
            theme_colors = (
                self.theme_manager.get_current_theme_colors()
                if self.theme_manager
                else {}
            )
            self.table.populate_data(
                self.processed_data,
                self.translations,
                debug_mode,
                exclude_names,
                theme_colors,
            )
            # Reapply table font after populate_data (stylesheet might override font)
            self.update_table_font(settings.get("font_size", 8))

        # Save theme preference
        settings = self.settings_manager.load_settings()
        settings["theme"] = theme_name
        self.settings_manager.save_settings(settings)

    def update_table_font(self, font_size):
        """Update table font size including headers and recalculate column widths"""
        font = QFont("Consolas", font_size)
        if not font.exactMatch():
            font = QFont("Courier New", font_size)
        if not font.exactMatch():
            font = QFont("Monospace", font_size)

        # Apply to table content first
        self.table.setFont(font)

        # Get header references and apply font more aggressively (work with container structure)
        main_table = (
            self.table.main_table if hasattr(self.table, "main_table") else self.table
        )
        h_header = main_table.horizontalHeader()
        v_header = main_table.verticalHeader()

        # Clear any existing stylesheets that might override font
        h_header.setStyleSheet("")
        v_header.setStyleSheet("")

        # Apply font to headers multiple times to ensure it takes
        h_header.setFont(font)
        v_header.setFont(font)

        # Force style updates
        h_header.style().unpolish(h_header)
        h_header.style().polish(h_header)
        v_header.style().unpolish(v_header)
        v_header.style().polish(v_header)

        # Force complete refresh of headers
        h_header.updateGeometry()
        v_header.updateGeometry()
        h_header.repaint()
        v_header.repaint()

        # Force table refresh
        self.table.updateGeometry()
        self.table.repaint()

        # Add a small delay and then recalculate column widths
        if hasattr(main_table, "rowCount") and main_table.rowCount() > 0:
            settings = self.settings_manager.load_settings()
            debug_mode = settings.get("debug", False)
            if debug_mode:
                print(
                    f"Debug: Recalculating column widths after font size change to {font_size}px"
                )
                print(
                    f"Debug: Header font after update: {h_header.font().pointSize()}px"
                )
                print(
                    f"Debug: Table font after update: {self.table.font().pointSize()}px"
                )

            # Update row heights to match new font size
            self.table.update_row_heights(debug_mode)

            # Force immediate column recalculation
            self.table.apply_minimal_column_sizing(debug_mode)

    def update_ui_font(self, font_size):
        """Update UI elements font size"""
        font = QFont()
        font.setPointSize(font_size)

        # Apply to main window first
        self.setFont(font)

        # Apply specifically to tabs and force refresh
        if hasattr(self, "tab_widget") and self.tab_widget:
            self.tab_widget.setFont(font)
            self.tab_widget.tabBar().setFont(font)

            # Force tab text refresh and apply font to tab contents
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if widget:
                    widget.setFont(font)
                    # Apply to all children except table
                    for child in widget.findChildren(QWidget):
                        if (
                            not hasattr(child, "objectName")
                            or child.objectName() != "table"
                        ):
                            if (
                                not isinstance(child, type(self.table))
                                if hasattr(self, "table")
                                else True
                            ):
                                child.setFont(font)

        # Apply specifically to all buttons and force text refresh
        for button in self.findChildren(QPushButton):
            # Clear any existing stylesheet that might override font
            current_style = button.styleSheet()
            button.setStyleSheet("")  # Temporarily clear stylesheet
            button.setFont(font)
            button.setStyleSheet(current_style)  # Restore stylesheet

            # Force complete button refresh
            button.updateGeometry()
            button.update()
            button.repaint()  # Force immediate repaint

        # Apply to all labels except status bar labels
        for label in self.findChildren(QLabel):
            # Skip status bar labels
            if hasattr(self, "status_bar"):
                parent = label.parent()
                while parent:
                    if parent == self.status_bar:
                        break
                    parent = parent.parent()
                else:
                    # Not in status bar
                    label.setFont(font)
            else:
                label.setFont(font)

        # Apply to menus
        if self.menuBar():
            self.menuBar().setFont(font)
            self._apply_font_to_menu_recursively(self.menuBar(), font)

    def _apply_font_to_menu_recursively(self, menu_container, font):
        """Recursively apply font to all menus and submenus"""
        for action in menu_container.actions():
            if action.menu():
                # Apply font to the menu itself
                action.menu().setFont(font)
                # Recursively apply to any submenus
                self._apply_font_to_menu_recursively(action.menu(), font)

    def setup_status_bar_font(self):
        """Set up status bar with standard 8px font and proper styling"""
        font = QFont()
        font.setPointSize(8)  # Standard 8px font for status bar

        # Apply standard font to status bar elements
        if hasattr(self, "status_info"):
            self.status_info.setFont(font)

        if hasattr(self, "ini_label"):
            self.ini_label.setFont(font)

        if hasattr(self, "api_label"):
            self.api_label.setFont(font)

        # Set standard status bar height
        self.status_bar.setFixedHeight(STATUS_BAR_HEIGHT)

    def load_data(self):
        """Load data for the latest instance of the configured meeting."""
        self._start_load(meeting_uuid=None)

    def load_meeting_instance(self, meeting_uuid):
        """Load data for a specific past meeting instance, identified by UUID."""
        self._start_load(meeting_uuid=meeting_uuid)

    def _start_load(self, meeting_uuid=None):
        """Shared loader: latest instance when meeting_uuid is None, otherwise
        the given past instance."""
        if not self.zoom_api:
            QMessageBox.warning(
                self,
                self.translations.get("warning_title"),
                self.translations.get("warning_no_api"),
            )
            return

        settings = self.settings_manager.load_settings()
        meeting_id = settings.get("meeting_id", "")

        if not meeting_id:
            QMessageBox.warning(
                self,
                self.translations.get("warning_title"),
                self.translations.get("warning_no_meeting_id"),
            )
            return

        self.current_meeting_uuid = meeting_uuid

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        # Disable buttons
        self.load_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.export_button.setEnabled(False)

        # Start worker thread
        debug_mode = settings.get("debug", False)
        self.worker = DataLoadWorker(
            self.zoom_api, meeting_id, debug_mode, meeting_uuid=meeting_uuid
        )
        self.worker.finished.connect(self.on_data_loaded)
        self.worker.error.connect(self.on_data_error)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.start()

    def show_past_meetings(self):
        """Open a calendar of past meeting instances and load the chosen one."""
        if not self.zoom_api:
            QMessageBox.warning(
                self,
                self.translations.get("warning_title"),
                self.translations.get("warning_no_api"),
            )
            return

        settings = self.settings_manager.load_settings()
        meeting_id = settings.get("meeting_id", "")
        if not meeting_id:
            QMessageBox.warning(
                self,
                self.translations.get("warning_title"),
                self.translations.get("warning_no_meeting_id"),
            )
            return

        import urllib.error

        instances = None
        err_code = None
        err_body = ""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            instances = self.zoom_api.get_past_meeting_instances(meeting_id)
        except urllib.error.HTTPError as e:
            err_code = e.code
            try:
                err_body = e.read().decode()
            except Exception:
                err_body = ""
        except Exception as e:
            err_body = str(e)
        finally:
            QApplication.restoreOverrideCursor()

        if instances is None:
            missing_scope = (
                ("list_past_instances" in err_body)
                or ("4711" in err_body)
                or ("scope" in err_body.lower())
            )
            if err_code in (400, 401) and missing_scope:
                QMessageBox.warning(
                    self,
                    self.translations.get("warning_title"),
                    self.translations.get("missing_scope_instances"),
                )
            else:
                QMessageBox.critical(
                    self,
                    self.translations.get("error_title"),
                    f"{self.translations.get('error_loading_data')}\n\n{err_body}",
                )
            return

        if not instances:
            QMessageBox.information(
                self,
                self.translations.get("past_meetings_title"),
                self.translations.get("no_past_meetings"),
            )
            return

        dialog = PastMeetingsDialog(self, instances, self.translations)
        if (
            dialog.exec() == PastMeetingsDialog.DialogCode.Accepted
            and dialog.selected_uuid
        ):
            self.load_meeting_instance(dialog.selected_uuid)

    def refresh_data(self):
        """Refresh current data (reloads the same instance, if one was chosen)."""
        self._start_load(meeting_uuid=getattr(self, "current_meeting_uuid", None))

    def on_progress_update(self, message):
        """Handle progress updates from worker thread"""
        self.status_label.setText(message)

    def on_data_loaded(self, data):
        """Handle successful data loading"""
        self.current_data = data

        # Store raw API data for debugging
        self.raw_api_data = {
            "meeting": data.get("meeting", {}),
            "participants": data.get("participants", []),
            "polls": data.get("polls", []),
        }

        # Store meeting metadata for exports
        meeting_info = data.get("meeting", {})
        self.meeting_data = {
            "meeting_id": meeting_info.get("id", "Unknown"),
            "topic": meeting_info.get("topic", "Unknown"),
            "start_time": meeting_info.get("start_time", ""),
            "duration": meeting_info.get("duration", 0),
        }

        # Process data
        settings = self.settings_manager.load_settings()
        exclude_names = settings.get("exclude_names", [])
        debug_mode = settings.get("debug", False)

        if debug_mode:
            print(
                f"Debug: Processing data with {len(data.get('participants', []))} participants and {len(data.get('polls', []))} polls"
            )

        # Extract participants and poll data
        participants = data.get("participants", [])
        polls = data.get("polls", [])  # This is now the questions array

        if debug_mode:
            print(f"Debug: Processing {len(polls)} poll responses")
            if polls and len(polls) > 0:
                print(f"Debug: Sample poll response: {polls[0]}")

        import re

        def extract_answer_number(answer_text):
            """Extract the leading integer from a poll answer (e.g. '2 άτομα' -> 2)."""
            match = re.search(r"^\s*(\d+)", str(answer_text))
            return int(match.group(1)) if match else None

        def format_time(dt_string):
            dt = parse_iso_datetime(dt_string)
            return dt.strftime("%H:%M:%S") if dt else "N/A"

        def is_anonymous_name(value):
            """Zoom returns anonymised poll answers under a name/email of
            'anonymous' (or 'Anonymous Attendee'), bucketing every vote into a
            single record's question_details. Detect that case."""
            return not value or str(value).strip().lower().startswith("anonymous")

        # Group participant connections by a stable identity so reconnections and
        # mid-meeting renames merge into one row. Zoom reports the display name
        # chosen at each join, so we key on the Zoom user id (falling back to
        # email, then name) and show the most recent name.
        def identity_key(p):
            return (
                (p.get("id") or "").strip()
                or (p.get("user_email") or "").strip().lower()
                or (p.get("name") or "").strip()
            )

        identity_groups = {}
        for p in participants:
            identity_groups.setdefault(identity_key(p), []).append(p)

        def aggregate_identity(conns):
            """Return (display_name, join, leave, reconnections) for one identity."""
            ordered = sorted(conns, key=lambda c: c.get("join_time", "") or "")
            display_name = ordered[-1].get("name", "") or ""  # most recent name
            join_time = format_time(ordered[0].get("join_time", ""))
            leave_time = format_time(ordered[-1].get("leave_time", ""))
            return display_name, join_time, leave_time, str(len(conns))

        # Poll respondents are reported by name, so map each display name used to
        # its identity key for lookups.
        name_to_key = {}
        for key, conns in identity_groups.items():
            for c in conns:
                nm = c.get("name") or ""
                if nm:
                    name_to_key.setdefault(nm, key)
        used_keys = set()  # identity keys already placed as a voter row

        # Process the poll data. Named respondents are matched to participants by
        # name; anonymised responses (all votes bucketed under one 'anonymous'
        # record) are collected separately so the total still reflects every vote.
        processed_details = {}
        anonymous_votes = []  # one integer per anonymous answer

        for question in polls:
            if not isinstance(question, dict):
                continue

            name = question.get("name", "")
            question_details = question.get("question_details", [])
            if not isinstance(question_details, list):
                question_details = []

            # Zoom no longer attributes anonymised polls to individuals: every
            # answer arrives under a single 'anonymous' record. Treat each entry
            # in question_details as one individual vote.
            if is_anonymous_name(name):
                for detail in question_details:
                    if not isinstance(detail, dict):
                        continue
                    number = extract_answer_number(detail.get("answer", ""))
                    if number is not None:
                        anonymous_votes.append(number)
                if debug_mode:
                    print(
                        f"Debug: Collected {len(question_details)} anonymous vote(s) from '{name}'"
                    )
                continue

            # Named respondent: use their highest numeric answer across all responses
            numbers = [
                extract_answer_number(d.get("answer", ""))
                for d in question_details
                if isinstance(d, dict)
            ]
            numbers = [n for n in numbers if n is not None]
            answer = str(max(numbers)) if numbers else "N/A"

            if debug_mode:
                print(f"Debug: {name} answered -> extracted: '{answer}'")

            # Match this poll respondent to a participant identity (by name) and
            # use the de-duplicated join/leave/reconnection info + latest name.
            key = name_to_key.get(name)
            if key is not None:
                used_keys.add(key)
                display_name, join_time, leave_time, reconn = aggregate_identity(
                    identity_groups[key]
                )
            else:
                display_name = name
                join_time = leave_time = reconn = "N/A"

            # Handle duplicate poll responses across records - keep the higher answer
            row_key = display_name
            if row_key in processed_details:
                old_num = extract_answer_number(processed_details[row_key][0]) or 0
                new_num = int(answer) if answer.isdigit() else 0

                if old_num != new_num and debug_mode:
                    print(
                        f"Debug: Duplicate poll participation for {row_key}: (1st: {processed_details[row_key][0]} | 2nd: {answer})"
                    )

                # Keep the higher answer
                if new_num > old_num:
                    processed_details[row_key] = [answer, join_time, leave_time, reconn]
            else:
                processed_details[row_key] = [answer, join_time, leave_time, reconn]

        # Add participant identities that didn't answer the poll (deduped; the
        # most recent display name is shown).
        for key, conns in identity_groups.items():
            if key in used_keys:
                continue
            display_name, join_time, leave_time, reconn = aggregate_identity(conns)
            if display_name not in processed_details:
                processed_details[display_name] = ["N/A", join_time, leave_time, reconn]

        # Calculate total from named answers (excluding excluded names)...
        poll_answers = []
        for name, details in processed_details.items():
            if name in exclude_names:
                continue
            if str(details[0]).isdigit():
                poll_answers.append(int(details[0]))
        total = sum(poll_answers)

        # ...plus every anonymous vote (these cannot be attributed to a name, so
        # they are surfaced as one aggregate summary row instead of being lost).
        if anonymous_votes:
            anon_sum = sum(anonymous_votes)
            total += anon_sum

            counts = {}
            for vote in anonymous_votes:
                counts[vote] = counts.get(vote, 0) + 1
            breakdown = ", ".join(f"{counts[v]}×{v}" for v in sorted(counts))
            label = self.translations.get("anonymous_responses", "Anonymous responses")
            anon_name = f"{label} ({len(anonymous_votes)}): {breakdown}"
            processed_details[anon_name] = [str(anon_sum), "", "", ""]

            if debug_mode:
                print(
                    f"Debug: Anonymous votes={len(anonymous_votes)} sum={anon_sum} breakdown='{breakdown}'"
                )

        if debug_mode:
            print(
                f"Debug: Total calculated: {total} (named numeric: {len(poll_answers)}, "
                f"anonymous votes: {len(anonymous_votes)}, excluded: {exclude_names})"
            )

        processed_details["Total"] = [str(total), "", "", ""]

        # Convert to list format for table display
        self.processed_data = []
        for name, details in processed_details.items():
            row = {
                "Name": name,
                "Poll Answer": details[0] if len(details) > 0 else "N/A",
                "Join Time": details[1] if len(details) > 1 else "N/A",
                "Leave Time": details[2] if len(details) > 2 else "N/A",
                "Reconnections": details[3] if len(details) > 3 else "N/A",
            }
            self.processed_data.append(row)

        # Update table with row coloring based on status
        theme_colors = (
            self.theme_manager.get_current_theme_colors() if self.theme_manager else {}
        )
        self.table.populate_data(
            self.processed_data,
            self.translations,
            debug_mode,
            exclude_names,
            theme_colors,
        )

        # Reapply table font after populate_data (stylesheet might override font)
        settings = self.settings_manager.load_settings()
        self.update_table_font(settings.get("font_size", 8))

        # Adjust window size to accommodate data
        self.adjust_window_size_for_data()

        # Update status
        self.update_status_info()

        # Hide progress bar
        self.progress_bar.setVisible(False)

        # Enable buttons
        self.load_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.export_button.setEnabled(True)
        self.send_button.setEnabled(True)
        self.email_sent = False  # Reset sent flag when new data is loaded

        # Enable all export actions
        self.export_csv_action.setEnabled(True)
        self.export_json_action.setEnabled(True)
        self.export_yaml_action.setEnabled(True)
        self.export_xml_action.setEnabled(True)

        # Enable debug menu
        if hasattr(self, "view_raw_data_action"):
            self.view_raw_data_action.setEnabled(True)

        # Clean up worker
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

        # An empty poll report often just means Zoom hasn't finalised it yet
        # (it can take a few minutes after a meeting ends). Show a non-blocking
        # message in the table area rather than a dialog the user must dismiss.
        if not polls:
            self.table.show_message(self.translations.get("poll_report_empty"))

    def on_data_error(self, error_message):
        """Handle data loading error"""
        QMessageBox.critical(
            self,
            self.translations.get("error_title"),
            f"{self.translations.get('error_loading_data')}\n\n{error_message}",
        )

        # Hide progress bar
        self.progress_bar.setVisible(False)

        # Enable buttons
        self.load_button.setEnabled(True)
        self.refresh_button.setEnabled(False)  # Keep disabled if no data
        self.export_button.setEnabled(False)  # Keep disabled if no data

        # Update status
        self.status_label.setText(self.translations.get("status_error"))

        # Clean up worker
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def _meeting_datetime(self):
        """Return the loaded instance's start as a local-aware datetime, or None.

        Falls back to the earliest participant join time when the meeting's own
        start time is unavailable.
        """
        start = ""
        if getattr(self, "meeting_data", None):
            start = self.meeting_data.get("start_time", "") or ""
        if not start and getattr(self, "current_data", None):
            joins = [
                p.get("join_time", "")
                for p in self.current_data.get("participants", [])
                if p.get("join_time")
            ]
            if joins:
                start = min(joins)
        dt = parse_iso_datetime(start) if start else None
        return dt.astimezone() if dt else None

    def _meeting_datetime_display(self):
        """Human-readable local date/time of the loaded instance ('' if unknown)."""
        dt = self._meeting_datetime()
        if not dt:
            return ""
        day_keys = [
            "day_mon",
            "day_tue",
            "day_wed",
            "day_thu",
            "day_fri",
            "day_sat",
            "day_sun",
        ]
        day_abbrev = self.translations.get(day_keys[dt.weekday()])
        return f"{day_abbrev}, {dt.strftime('%d.%m.%Y %H:%M')}"

    def update_status_info(self):
        """Update status information"""
        if self.current_data:
            poll_count = len(self.current_data.get("polls", []))
            participant_count = len(self.current_data.get("participants", []))
            meeting = self.current_data.get("meeting", {})
            meeting_topic = meeting.get("topic", "Unknown")

            status_text = self.translations.get("status_data_loaded").format(
                polls=poll_count, participants=participant_count, meeting=meeting_topic
            )
            self.status_label.setText(status_text)

            when = self._meeting_datetime_display()
            counts = f"{poll_count} polls | {participant_count} participants | {len(self.processed_data)} records"
            self.status_info.setText(f"{when}  |  {counts}" if when else counts)
        else:
            self.status_label.setText(self.translations.get("status_ready"))
            self.status_info.setText("")

    def adjust_window_size_for_data(self):
        """Adjust window size to better accommodate loaded data"""
        if not self.processed_data:
            return

        # Get settings for debug mode
        settings = self.settings_manager.load_settings()
        debug_mode = settings.get("debug", False)

        # Get actual row height from table if possible
        if self.table.main_table.rowCount() > 0:
            actual_row_height = self.table.main_table.rowHeight(0)
        else:
            actual_row_height = 8  # Use our compact row height as fallback

        # Get actual header height
        header_height = self.table.main_table.horizontalHeader().height()

        # Calculate UI overhead more accurately
        menu_height = self.menuBar().height() if self.menuBar() else 0
        toolbar_height = TOOLBAR_HEIGHT  # Estimate for toolbar
        status_bar_height = (
            self.status_bar.height()
            if hasattr(self, "status_bar")
            else STATUS_BAR_HEIGHT
        )
        progress_bar_height = PROGRESS_BAR_HEIGHT  # For progress bar and status label
        margins_padding = WINDOW_MARGINS_PADDING  # Window margins and padding

        ui_overhead = (
            menu_height
            + toolbar_height
            + status_bar_height
            + progress_bar_height
            + margins_padding
        )

        # Set reasonable bounds - minimum and maximum based on constants
        min_height = MIN_TABLE_HEIGHT
        max_height = MAX_TABLE_HEIGHT  # Increased maximum

        # Calculate maximum rows that can fit within max_height
        available_height = max_height - ui_overhead - header_height
        max_rows_that_fit = max(1, int(available_height / actual_row_height))

        # Use all available data rows up to what can fit in the window
        row_count = min(len(self.processed_data), max_rows_that_fit)

        # Calculate desired height
        table_content_height = (row_count * actual_row_height) + header_height
        desired_height = table_content_height + ui_overhead

        current_width = self.width()
        current_height = self.height()

        new_height = max(min_height, min(desired_height, max_height))

        if debug_mode:
            print("Debug: Window resize calculation:")
            print(f"  Available data rows: {len(self.processed_data)}")
            print(f"  Max height limit: {max_height}px")
            print(f"  Available height for rows: {available_height}px")
            print(f"  Max rows that can fit: {max_rows_that_fit}")
            print(f"  Showing rows: {row_count}")
            print(f"  Row height: {actual_row_height}px")
            print(f"  Header height: {header_height}px")
            print(f"  UI overhead: {ui_overhead}px")
            print(f"  Desired height: {desired_height}px")
            print(f"  Current size: {current_width}x{current_height}")
            print(f"  New size: {current_width}x{new_height}")

        # Only resize if the height difference is significant (more than threshold)
        if abs(new_height - current_height) > RESIZE_THRESHOLD:
            if debug_mode:
                print(f"  Resizing window from {current_height}px to {new_height}px")
            self.resize(current_width, new_height)
        elif debug_mode:
            print(
                f"  No resize needed (difference: {abs(new_height - current_height)}px)"
            )

    def export_data(self, export_format=None):
        """Export data in specified format using ExportManager"""
        if not self.processed_data:
            QMessageBox.warning(
                self,
                self.translations.get("warning_title"),
                self.translations.get("warning_no_data"),
            )
            return

        # Use default format from settings if not specified
        if export_format is None:
            settings = self.settings_manager.load_settings()
            export_format = settings.get("export_format", "csv")
            debug_mode = settings.get("debug", False)
            if debug_mode:
                print(
                    f"Debug: Using default export format from settings: {export_format}"
                )
        else:
            settings = self.settings_manager.load_settings()
            debug_mode = settings.get("debug", False)
            if debug_mode:
                print(f"Debug: Using specified export format: {export_format}")

        # Get default filename from ExportManager
        default_filename = self.export_manager.get_default_filename(export_format)

        # Set up file dialog filters
        filters = {
            "csv": "CSV Files (*.csv)",
            "json": "JSON Files (*.json)",
            "yaml": "YAML Files (*.yaml *.yml)",
            "xml": "XML Files (*.xml)",
        }

        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.translations.get("export_dialog_title"),
            default_filename,
            filters.get(export_format, "All Files (*.*)"),
        )

        if filename:
            try:
                # Prepare export settings
                settings = self.settings_manager.load_settings()
                csv_separator = settings.get("csv_separator", ";")

                # Set CSV separator for ExportManager
                self.export_manager.set_csv_separator(csv_separator)

                # Add meeting metadata if available
                metadata = {}
                if hasattr(self, "meeting_data") and self.meeting_data:
                    metadata.update(self.meeting_data)

                # Convert processed data to the format expected by ExportManager (List[Dict])
                export_data = []
                for item in self.processed_data:
                    export_item = {
                        "name": item.get("Name", "Unknown"),
                        "answer": item.get("Poll Answer", "No Answer"),
                        "join_time": item.get("Join Time", "N/A"),
                        "leave_time": item.get("Leave Time", "N/A"),
                        "reconnections": item.get("Reconnections", "N/A"),
                    }
                    # Add any poll results if available
                    if "poll_results" in item:
                        export_item["poll_results"] = item["poll_results"]
                    export_data.append(export_item)

                # Export using ExportManager
                success = self.export_manager.export_data(
                    data=export_data,
                    filename=filename,
                    format_type=export_format,
                    metadata=metadata,
                )

                if success:
                    QMessageBox.information(
                        self,
                        self.translations.get("info_title"),
                        self.translations.get("export_success").format(
                            filename=filename
                        ),
                    )
                else:
                    QMessageBox.critical(
                        self,
                        self.translations.get("error_title"),
                        self.translations.get("export_error"),
                    )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    self.translations.get("error_title"),
                    f"{self.translations.get('export_error')}\n\n{str(e)}",
                )

    def view_raw_data(self):
        """Show raw API data dialog for debugging"""
        if not hasattr(self, "raw_api_data") or not self.raw_api_data:
            QMessageBox.warning(
                self,
                "Debug",
                "No raw API data available. Please load meeting data first.",
            )
            return

        settings = self.settings_manager.load_settings()
        font_size = settings.get("font_size", 8)
        dialog = RawDataDialog(self, self.raw_api_data, self.translations, font_size)
        dialog.exec()

    def build_email_html(self) -> str:
        """Build an HTML table of the poll results for emailing"""
        meeting_info = ""
        if hasattr(self, "meeting_data") and self.meeting_data:
            topic = self.meeting_data.get("topic", "")
            when = self._meeting_datetime_display()
            if topic or when:
                meeting_info = "<p>"
                if topic:
                    meeting_info += f"<strong>{topic}</strong>"
                    if when:
                        meeting_info += " &mdash; "
                if when:
                    meeting_info += when
                meeting_info += "</p>"

        # Use translated column headers
        columns = ["Name", "Poll Answer", "Join Time", "Leave Time", "Reconnections"]
        translated_columns = [
            self.translations.get("table_header_name"),
            self.translations.get("table_header_poll_answer"),
            self.translations.get("table_header_join_time"),
            self.translations.get("table_header_leave_time"),
            self.translations.get("table_header_reconnections"),
        ]

        header_cells = "".join(
            f'<th style="border:1px solid #ccc;padding:6px 10px;background:#4472C4;color:#fff;text-align:left;">'
            f"{col}</th>"
            for col in translated_columns
        )

        settings = self.settings_manager.load_settings()
        exclude_names = settings.get("exclude_names", [])

        rows_html = ""
        for row in self.processed_data:
            name = row.get("Name", "")
            poll_answer = row.get("Poll Answer", "")

            if name == "Total":
                bg = "#D9E1F2"
                text_color = "#333333"
            elif name in exclude_names:
                bg = "#e0e0e0"
                text_color = "#666666"
            elif poll_answer and poll_answer != "N/A":
                bg = "#e8f5e8"
                text_color = "#2d5a2d"
            else:
                bg = "#ffe8e8"
                text_color = "#5a2d2d"

            cells = "".join(
                f'<td style="border:1px solid #ccc;padding:4px 10px;color:{text_color};">{row.get(col, "")}</td>'
                for col in columns
            )
            rows_html += f'<tr style="background:{bg};">{cells}</tr>'

        html = f"""
        <html><body style="font-family:Arial,sans-serif;font-size:13px;">
        {meeting_info}
        <table style="border-collapse:collapse;min-width:500px;">
          <thead><tr>{header_cells}</tr></thead>
          <tbody>{rows_html}</tbody>
        </table>
        </body></html>
        """
        return html

    def send_email(self):
        """Send poll results via email to configured recipients"""
        if not self.processed_data:
            QMessageBox.warning(
                self,
                self.translations.get("warning_title"),
                self.translations.get("email_no_data"),
            )
            return

        settings = self.settings_manager.load_settings()
        recipients = settings.get("email_recipients", [])
        smtp_server = settings.get("smtp_server", "")
        smtp_port = settings.get("smtp_port", 587)
        smtp_username = settings.get("smtp_username", "")
        smtp_password = settings.get("smtp_password", "")
        smtp_use_tls = settings.get("smtp_use_tls", True)

        if not recipients:
            QMessageBox.warning(
                self,
                self.translations.get("warning_title"),
                self.translations.get("email_no_recipients"),
            )
            return

        if not smtp_server:
            QMessageBox.warning(
                self,
                self.translations.get("warning_title"),
                self.translations.get("email_no_smtp"),
            )
            return

        self.status_label.setText(self.translations.get("email_sending"))
        QApplication.processEvents()

        try:
            html_body = self.build_email_html()

            # Build subject from the meeting's own local date/time:
            # "ZPA - <day>, <date> <time>"
            subject = "ZPA"
            when = self._meeting_datetime_display()
            if when:
                subject = f"ZPA - {when}"

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_username
            msg["To"] = ", ".join(recipients)
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            if smtp_use_tls:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15)

            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)

            server.sendmail(smtp_username, recipients, msg.as_string())
            server.quit()

            self.email_sent = True
            QMessageBox.information(
                self,
                self.translations.get("info_title"),
                self.translations.get("email_sent_success").format(
                    recipients="\n".join(recipients)
                ),
            )
            self.update_status_info()

        except Exception as exc:
            QMessageBox.critical(
                self,
                self.translations.get("error_title"),
                self.translations.get("email_send_error").format(error=str(exc)),
            )
            self.update_status_info()

    def show_about(self):
        """Show about dialog"""
        about_text = self.translations.get("about_text")
        QMessageBox.about(self, self.translations.get("about_title"), about_text)

    def closeEvent(self, event):
        """Handle application close event"""
        # Clean up worker threads if running
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        if (
            getattr(self, "conn_worker", None) is not None
            and self.conn_worker.isRunning()
        ):
            self.conn_worker.terminate()
            self.conn_worker.wait()

        event.accept()


def main():
    """Main application entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        prog="zoom-poll-analyzer",
        description="Zoom Poll Analyzer - Analyze and export Zoom meeting poll results",
        epilog="""
Examples:
  %(prog)s                           # Run with default settings
  %(prog)s --ini-file custom.ini     # Use custom INI file
  %(prog)s --help                    # Show this help message

The application will create a default INI file if none exists.
Configuration includes Zoom API credentials, display preferences, and export settings.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--ini-file",
        type=str,
        metavar="PATH",
        help="Path to custom INI configuration file (default: ZoomPollAnalyzer.ini in project root)",
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    args = parser.parse_args()

    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Zoom Poll Analyzer")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Zoom Poll Analyzer")

    # Create and show main window with optional custom INI file
    window = ZoomPollAnalyzer(ini_file_path=args.ini_file)
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
