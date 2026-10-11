"""
Status LED component for displaying colored status indicators.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QLabel

# Constants for StatusLED
LED_SIZE = 10  # Final size: 10px
LED_PADDING = 1  # Reduced proportionally
LED_HIGHLIGHT_SIZE = 3  # Reduced proportionally
LED_HIGHLIGHT_OFFSET = 2  # Reduced proportionally

# Status colors
COLOR_GREEN = QColor(0, 200, 0)
COLOR_RED = QColor(255, 0, 0)
COLOR_GRAY = QColor(128, 128, 128)


class StatusLED(QLabel):
    """Custom widget to display a colored status LED"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(LED_SIZE, LED_SIZE)
        self._color = COLOR_GRAY  # Default gray (unknown state)
        self._status = "unknown"

        # Set a unique object name for CSS targeting
        self.setObjectName("StatusLED")

        # Force override any CSS that might interfere with custom painting
        # Use QLabel selector with object name and !important declarations
        self.setStyleSheet("""
            QLabel#StatusLED {
                background: transparent !important;
                border: none !important;
                border-radius: 0px !important;
                padding: 0px !important;
                margin: 0px !important;
                min-width: 10px !important;
                max-width: 10px !important;
                min-height: 10px !important;
                max-height: 10px !important;
                outline: none !important;
            }
        """)

        # Force repaint to ensure consistent initial appearance
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

        # Also try to disable any automatic styling
        self.setAutoFillBackground(False)

    def set_status(self, status: str):
        """Set LED status: 'ok'/'connected' (green), 'error' (red), 'unknown' (gray)"""
        self._status = status
        if status in ("ok", "connected"):
            self._color = COLOR_GREEN
        elif status == "error":
            self._color = COLOR_RED
        else:  # unknown
            self._color = COLOR_GRAY
        self.update()

    def resizeEvent(self, event):
        """Override resize to maintain fixed size"""
        super().resizeEvent(event)
        # Force the widget to stay at LED_SIZE
        if self.size().width() != LED_SIZE or self.size().height() != LED_SIZE:
            self.setFixedSize(LED_SIZE, LED_SIZE)

    def showEvent(self, event):
        """Override show event to ensure proper initial painting"""
        super().showEvent(event)
        # Force a repaint when the widget becomes visible
        self.update()

    def paintEvent(self, event):
        """Custom paint event to draw the LED"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Clear the widget completely to ensure consistent background
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)

        # Get the actual widget size for calculations
        widget_width = self.width()
        widget_height = self.height()

        # Calculate circle parameters based on actual widget size
        min_dimension = min(widget_width, widget_height)
        circle_size = min_dimension - 2 * LED_PADDING

        # Center the circle in the widget
        x_offset = (widget_width - circle_size) // 2
        y_offset = (widget_height - circle_size) // 2

        # Draw LED circle
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)
        painter.drawEllipse(x_offset, y_offset, circle_size, circle_size)

        # Draw inner highlight (adjust position based on actual size)
        highlight_size = max(2, circle_size // 4)  # Scale highlight with circle size
        highlight_x = x_offset + 2
        highlight_y = y_offset + 2

        highlight_color = self._color.lighter(150)
        painter.setBrush(highlight_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(highlight_x, highlight_y, highlight_size, highlight_size)
