"""
Past Meetings Dialog: pick a past meeting instance from a calendar.

Days that had a meeting are highlighted in green. Selecting a day lists that
day's session(s); choosing one returns its UUID to the caller so the main
window can load that instance.
"""

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor, QFont, QPen
from PyQt6.QtWidgets import (
    QCalendarWidget,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from ..core.data_processor import parse_iso_datetime


class _MeetingCalendar(QCalendarWidget):
    """Calendar that fills the background of days that had a meeting green."""

    def __init__(self, marked_dates, bg_color, parent=None):
        super().__init__(parent)
        self._marked = marked_dates  # set of (year, month, day) tuples
        self._bg = QColor(bg_color)
        self._text = QColor("white")
        self._sel = QColor("#0d3b1e")

    def paintCell(self, painter, rect, date):
        if (date.year(), date.month(), date.day()) in self._marked:
            painter.save()
            painter.fillRect(rect, self._bg)
            if date == self.selectedDate():
                pen = QPen(self._sel)
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawRect(rect.adjusted(1, 1, -2, -2))
            painter.setPen(self._text)
            painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), str(date.day()))
            painter.restore()
        else:
            super().paintCell(painter, rect, date)


class PastMeetingsDialog(QDialog):
    """Calendar-based picker for past meeting instances."""

    MIN_YEAR = 2024
    MIN_MONTH = 6  # June 2024

    # English fallback for the 3-letter month abbreviations (index 1..12)
    _MONTH_ABBR_EN = (
        "",
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    )

    def __init__(self, parent=None, instances=None, translations=None):
        super().__init__(parent)
        self.translations = translations
        self.selected_uuid = None
        self.selected_start_time = None

        # Parse instances into local datetimes and index them by calendar day
        self._by_day = {}  # (y, m, d) -> list of {'uuid', 'start_time', 'dt'}
        for inst in instances or []:
            dt = parse_iso_datetime(inst.get("start_time", ""))
            if dt is None:
                continue
            local = dt.astimezone()  # convert UTC -> local time
            key = (local.year, local.month, local.day)
            self._by_day.setdefault(key, []).append(
                {
                    "uuid": inst.get("uuid", ""),
                    "start_time": inst.get("start_time", ""),
                    "dt": local,
                }
            )
        for items in self._by_day.values():
            items.sort(key=lambda x: x["dt"])

        # Inherit UI font size from the parent window if available
        ui_font_size = 9
        if parent is not None and hasattr(parent, "settings_manager"):
            try:
                ui_font_size = parent.settings_manager.load_settings().get(
                    "ui_font_size", 9
                )
            except Exception:
                ui_font_size = 9
        self.setFont(QFont("", ui_font_size))

        self._build_ui(marked=set(self._by_day.keys()))
        self._select_initial_day()

    def _t(self, key, default):
        if self.translations is not None:
            value = self.translations.get(key, default)
            if value and value != key:
                return value
        return default

    def _build_ui(self, marked):
        self.setWindowTitle(self._t("past_meetings_title", "Load Past Meeting"))
        self.setModal(True)
        self.resize(460, 460)

        layout = QVBoxLayout(self)

        info = QLabel(
            self._t(
                "past_meetings_info",
                "Pick a day with a meeting (highlighted in green), then choose the session.",
            )
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        today = QDate.currentDate()

        self.calendar = _MeetingCalendar(marked, "#2d9d4a", self)
        self.calendar.setGridVisible(True)
        self.calendar.setNavigationBarVisible(False)
        self.calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.calendar.setMinimumDate(QDate(self.MIN_YEAR, self.MIN_MONTH, 1))
        self.calendar.setMaximumDate(
            QDate(today.year(), today.month(), today.daysInMonth())
        )
        self.calendar.selectionChanged.connect(self._on_day_changed)
        self.calendar.currentPageChanged.connect(self._sync_nav_from_calendar)

        # Month + year dropdown navigation (replaces the built-in navigation bar)
        nav_layout = QHBoxLayout()
        self.month_combo = QComboBox()
        self.year_combo = QComboBox()
        for y in range(self.MIN_YEAR, today.year() + 1):
            self.year_combo.addItem(str(y), y)
        yidx = self.year_combo.findData(today.year())
        if yidx >= 0:
            self.year_combo.setCurrentIndex(yidx)
        self._populate_month_combo(today.year(), today.month())
        nav_layout.addWidget(self.month_combo)
        nav_layout.addWidget(self.year_combo)
        nav_layout.addStretch()
        layout.addLayout(nav_layout)
        layout.addWidget(self.calendar)

        self.year_combo.currentIndexChanged.connect(self._on_nav_changed)
        self.month_combo.currentIndexChanged.connect(self._on_nav_changed)

        self.list_label = QLabel(self._t("select_instance", "Sessions on this day:"))
        layout.addWidget(self.list_label)

        self.session_list = QListWidget()
        self.session_list.itemSelectionChanged.connect(self._on_session_selected)
        self.session_list.itemDoubleClicked.connect(
            lambda _item: self._accept_if_ready()
        )
        layout.addWidget(self.session_list)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(
            self._t("past_meeting_load", "Load")
        )
        self.buttons.accepted.connect(self._accept_if_ready)
        self.buttons.rejected.connect(self.reject)
        self._ok_button = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_button.setEnabled(False)
        layout.addWidget(self.buttons)

    def _month_abbr(self, m):
        """Return the translated 3-letter abbreviation for month *m* (1..12)."""
        return self._t(f"month_abbr_{m}", self._MONTH_ABBR_EN[m])

    def _populate_month_combo(self, year, select_month):
        """Fill the month dropdown with the valid months for *year*."""
        today = QDate.currentDate()
        start = self.MIN_MONTH if year <= self.MIN_YEAR else 1
        end = today.month() if year >= today.year() else 12
        self.month_combo.blockSignals(True)
        self.month_combo.clear()
        for m in range(start, end + 1):
            self.month_combo.addItem(self._month_abbr(m), m)
        idx = self.month_combo.findData(select_month)
        self.month_combo.setCurrentIndex(
            idx if idx >= 0 else self.month_combo.count() - 1
        )
        self.month_combo.blockSignals(False)

    def _on_nav_changed(self):
        """Navigate the calendar when a dropdown changes."""
        year = self.year_combo.currentData()
        if year is None:
            return
        month = self.month_combo.currentData() or QDate.currentDate().month()
        self._populate_month_combo(year, month)
        month = self.month_combo.currentData()
        if month:
            self.calendar.setCurrentPage(year, month)

    def _sync_nav_from_calendar(self, year, month):
        """Keep the dropdowns in sync when the calendar page changes."""
        self.year_combo.blockSignals(True)
        yidx = self.year_combo.findData(year)
        if yidx >= 0:
            self.year_combo.setCurrentIndex(yidx)
        self.year_combo.blockSignals(False)
        self._populate_month_combo(year, month)

    def _select_initial_day(self):
        """Select the most recent meeting day and populate its sessions."""
        if not self._by_day:
            return
        y, m, d = max(self._by_day.keys())
        self.calendar.setSelectedDate(QDate(y, m, d))
        self._on_day_changed()

    def _on_day_changed(self):
        self.session_list.clear()
        self._ok_button.setEnabled(False)
        date = self.calendar.selectedDate()
        key = (date.year(), date.month(), date.day())
        for entry in self._by_day.get(key, []):
            item = QListWidgetItem(entry["dt"].strftime("%H:%M"))
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.session_list.addItem(item)
        # Auto-select when there is exactly one session that day
        if self.session_list.count() == 1:
            self.session_list.setCurrentRow(0)

    def _on_session_selected(self):
        item = self.session_list.currentItem()
        if item is None:
            self.selected_uuid = None
            self._ok_button.setEnabled(False)
            return
        entry = item.data(Qt.ItemDataRole.UserRole)
        self.selected_uuid = entry.get("uuid")
        self.selected_start_time = entry.get("start_time")
        self._ok_button.setEnabled(bool(self.selected_uuid))

    def _accept_if_ready(self):
        if self.selected_uuid:
            self.accept()
