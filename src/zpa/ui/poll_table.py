"""
Table widget for displaying poll data with separate total row.
"""

from typing import Dict, List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QHeaderView,
    QLabel,
    QSizePolicy,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class PollTableItem(QTableWidgetItem):
    """Keep response groups together while sorting within each group."""

    def __lt__(self, other):
        ranks = {"answered": 0, "excluded": 1, "no_answer": 2, "total": 3}
        own_rank = ranks.get(self.data(Qt.ItemDataRole.UserRole), 2)
        other_rank = ranks.get(other.data(Qt.ItemDataRole.UserRole), 2)
        if own_rank != other_rank:
            table = self.tableWidget()
            descending = (
                table is not None
                and table.horizontalHeader().sortIndicatorOrder()
                == Qt.SortOrder.DescendingOrder
            )
            return own_rank > other_rank if descending else own_rank < other_rank
        return self.text().casefold() < other.text().casefold()


class ColoredItemDelegate(QStyledItemDelegate):
    """Custom delegate to ensure row colors are painted correctly"""

    def paint(self, painter, option, index):
        """Custom paint method that respects our background colors"""
        # Get the item's background color
        background = index.data(Qt.ItemDataRole.BackgroundRole)

        if background and isinstance(background, QColor):
            # Fill the entire cell with the background color
            painter.fillRect(option.rect, background)

            # Set text color for contrast
            foreground = index.data(Qt.ItemDataRole.ForegroundRole)
            if foreground and isinstance(foreground, QColor):
                option.palette.setColor(option.palette.ColorRole.Text, foreground)

        # Call the parent to draw the text
        super().paint(painter, option, index)


class TotalRowWidget(QTableWidget):
    """Widget to display the total row separately"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_total_table()

    def setup_total_table(self):
        """Setup the total row table"""
        self.setRowCount(1)
        self.setMaximumHeight(30)  # Fixed height for one row
        self.setMinimumHeight(30)

        # Hide horizontal header but show vertical header to align with main table
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(True)

        # Set empty label for the vertical header to match main table alignment
        self.setVerticalHeaderLabels([""])

        # Match vertical header width with main table (will be synced later)
        self.verticalHeader().setDefaultSectionSize(8)  # Match row height

        # Disable selection and interaction
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Match styling with main table
        self.setAlternatingRowColors(False)

        # Disable scrollbars and eliminate extra space
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Set fixed size policy for total row
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Eliminate any extra margins
        self.setContentsMargins(0, 0, 0, 0)

        # Set exact height for single row
        self.setMaximumHeight(30)  # Adjust based on font size
        self.setMinimumHeight(30)

        # Set exact height for single row
        self.setMaximumHeight(30)  # Adjust based on font size
        self.setMinimumHeight(30)

    def sync_columns_with_main_table(self, main_table):
        """Sync column count and widths with main table"""
        # Set same number of columns
        self.setColumnCount(main_table.columnCount())

        # Don't set up resize modes for total row - just copy exact widths
        # This prevents conflicts with the main table's stretch behavior

        # Copy exact column widths from main table
        for col in range(self.columnCount()):
            width = main_table.columnWidth(col)
            self.setColumnWidth(col, width)

        # Set same font as main table
        self.setFont(main_table.font())

        # Sync vertical header width with main table
        main_v_header_width = main_table.verticalHeader().width()
        self.verticalHeader().setFixedWidth(main_v_header_width)

        # Set row height to match main table
        if main_table.rowCount() > 0:
            row_height = main_table.rowHeight(0)
            self.setRowHeight(0, row_height)
            # Also update the total row widget's fixed height
            header_height = self.horizontalHeader().height()
            total_height = row_height + header_height + 4  # Small padding
            self.setMaximumHeight(total_height)
            self.setMinimumHeight(total_height)


class PollTableContainer(QWidget):
    """Container widget that holds both the main table and total row"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_container()

    def setup_container(self):
        """Setup the container layout"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # No gap between main table and total row

        # Create main data table
        self.main_table = PollTable()
        self.main_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        # Create total row widget
        self.total_row = TotalRowWidget()
        self.total_row.setVisible(
            False
        )  # Hide total row initially until data is loaded
        self.total_row.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        # Add to layout
        layout.addWidget(self.main_table, 1)  # Main table gets stretch
        layout.addWidget(self.total_row, 0)  # Total row fixed size

        # Message shown in place of the table (e.g. when a poll report is empty)
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setContentsMargins(24, 24, 24, 24)
        message_font = self.message_label.font()
        message_font.setPointSize(11)
        message_font.setItalic(True)
        self.message_label.setFont(message_font)
        self.message_label.setVisible(False)
        layout.addWidget(self.message_label, 1)

        self.setLayout(layout)

        # Connect signal to auto-sync column widths when main table changes
        self.main_table.horizontalHeader().sectionResized.connect(
            self.on_main_table_column_resized
        )

    def show_message(self, text: str):
        """Show a centered, non-blocking message in place of the table."""
        self.message_label.setText(text)
        self.message_label.setVisible(True)
        self.main_table.setVisible(False)
        self.total_row.setVisible(False)

    def clear_message(self):
        """Hide the message and restore the table view."""
        self.message_label.setVisible(False)
        self.main_table.setVisible(True)

    def populate_data(
        self,
        data: List[Dict],
        translations,
        debug_mode: bool = False,
        exclude_names: List[str] = None,
        theme_colors: Dict[str, str] = None,
    ):
        """Populate both main table and total row"""
        # A fresh populate always replaces any standalone message
        self.clear_message()
        if not data:
            # No data - hide total row
            self.total_row.setVisible(False)
            return

        # Separate total row from main data
        main_data = []
        total_data = None

        for row in data:
            if row.get("Name") == "Total":
                total_data = row
            else:
                main_data.append(row)

        # Populate main table (without Total row)
        self.main_table.populate_data(
            main_data, translations, debug_mode, exclude_names, theme_colors
        )

        # Show/hide and populate total row based on data availability
        if (
            total_data and main_data
        ):  # Only show total row if we have both main data and total data
            self.total_row.setVisible(True)
            self.populate_total_row(total_data, theme_colors)
        else:
            self.total_row.setVisible(False)

        # Sync column widths only if total row is visible
        if self.total_row.isVisible():
            self.sync_column_widths()

    def populate_total_row(self, total_data: Dict, theme_colors: Dict[str, str] = None):
        """Populate the total row widget"""
        self.total_row.sync_columns_with_main_table(self.main_table)

        # Use values in dict order (matches column order in the table)
        values = list(total_data.values())

        # Populate total row data
        for col in range(min(len(values), self.total_row.columnCount())):
            value = values[col]
            item = QTableWidgetItem(str(value))

            # Set text alignment to match main table - left for Name column (col 0), center for all others
            if col == 0:  # Name column
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )
            else:  # All other columns
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                )

            # Apply neutral styling for total row
            if theme_colors:
                # Use theme colors
                bg_color = theme_colors.get("poll_row_total", "#f0f0f0")
                text_color = theme_colors.get("poll_row_total_text", "#333333")
                item.setBackground(QColor(bg_color))
                item.setForeground(QColor(text_color))
            else:
                # Fallback to default colors
                item.setBackground(QColor(240, 240, 240))
                item.setForeground(QColor(0, 0, 0))

            self.total_row.setItem(0, col, item)

    def sync_column_widths(self):
        """Synchronize column widths between main table and total row"""
        if self.total_row.isVisible():
            self.total_row.sync_columns_with_main_table(self.main_table)

    def on_main_table_column_resized(self, logical_index, old_size, new_size):
        """Slot to handle main table column resize and sync total row"""
        if self.total_row.isVisible() and logical_index < self.total_row.columnCount():
            self.total_row.setColumnWidth(logical_index, new_size)

    def apply_minimal_column_sizing(self, debug_mode=False):
        """Apply minimal column sizing to main table and sync total row"""
        self.main_table.apply_minimal_column_sizing(debug_mode)
        if self.total_row.isVisible():
            self.sync_column_widths()

    def update_row_heights(self, debug_mode=False):
        """Update row heights in both tables"""
        self.main_table.update_row_heights(debug_mode)
        # Sync total row height only if visible
        if self.total_row.isVisible() and self.main_table.rowCount() > 0:
            row_height = self.main_table.rowHeight(0)
            self.total_row.setRowHeight(0, row_height)

    def setFont(self, font):
        """Set font for both tables"""
        self.main_table.setFont(font)
        self.total_row.setFont(font)

    def populate_test_data(self):
        """Populate with test data"""
        self.main_table.populate_test_data()


class PollTable(QTableWidget):
    """Customized table widget for poll data display"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()

    def setup_table(self):
        """Initialize table settings"""
        self.setAlternatingRowColors(False)  # Disabled to allow custom row colors
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setSortingEnabled(True)
        self.horizontalHeader().setSortIndicator(0, Qt.SortOrder.AscendingOrder)

        # Enable horizontal scrolling when content is wider than available space
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Set custom delegate to ensure colors are painted
        self.setItemDelegate(ColoredItemDelegate(self))

        # Set headers to resize content but stretch name column to fill
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # The name column (typically column 0) should stretch to fill remaining space
        # We'll set this after we know the column structure in populate_data

        # Set vertical header to fixed size mode to maintain our compact row height
        v_header = self.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        # Font will be set by parent window based on settings
        # Don't set default font here - let it be controlled by settings

        # Set very compact row height
        self.verticalHeader().setDefaultSectionSize(8)

    def _get_row_colors(
        self,
        name: str,
        poll_answer: str,
        exclude_names: list,
        theme_colors: dict = None,
    ):
        """Get background and text colors for a row based on its state"""
        if name == "Total":
            # Total row - no background color (handled in total row widget)
            return None, None
        elif name in exclude_names:
            # Excluded names - gray colors
            if theme_colors:
                bg_color = QColor(theme_colors.get("poll_row_excluded", "#e0e0e0"))
                text_color = QColor(
                    theme_colors.get("poll_row_excluded_text", "#666666")
                )
            else:
                bg_color = QColor(220, 220, 220)
                text_color = QColor(102, 102, 102)
        elif poll_answer and poll_answer != "N/A":
            # Has answer - green colors
            if theme_colors:
                bg_color = QColor(theme_colors.get("poll_row_answered", "#e8f5e8"))
                text_color = QColor(
                    theme_colors.get("poll_row_answered_text", "#2d5a2d")
                )
            else:
                bg_color = QColor(200, 255, 200)
                text_color = QColor(45, 90, 45)
        else:
            # No answer - red colors
            if theme_colors:
                bg_color = QColor(theme_colors.get("poll_row_no_answer", "#ffe8e8"))
                text_color = QColor(
                    theme_colors.get("poll_row_no_answer_text", "#5a2d2d")
                )
            else:
                bg_color = QColor(255, 200, 200)
                text_color = QColor(90, 45, 45)

        return bg_color, text_color

    def populate_data(
        self,
        data: List[Dict],
        translations,
        debug_mode: bool = False,
        exclude_names: List[str] = None,
        theme_colors: Dict[str, str] = None,
    ):
        """Populate table with poll data and apply row background colors"""
        if not data:
            return

        exclude_names = exclude_names or []

        if debug_mode:
            print(f"Debug: Populating table with {len(data)} rows")
            if data:
                print(f"Debug: First row keys: {list(data[0].keys())}")
            print(f"Debug: Exclude names: {exclude_names}")
            print(f"Debug: Theme colors provided: {theme_colors is not None}")
            print(
                f"Debug: Alternating row colors disabled: {not self.alternatingRowColors()}"
            )

        # Get headers from first row
        headers = list(data[0].keys())

        # Set table dimensions
        self.setSortingEnabled(False)
        self.setRowCount(len(data))
        self.setColumnCount(len(headers))

        # Translate headers if possible
        translated_headers = []
        for header in headers:
            # Try to get translation for common headers
            translation_key = f"table_header_{header.lower().replace(' ', '_')}"
            translated = translations.get(translation_key)
            translated_headers.append(
                translated if translated != translation_key else header
            )

        self.setHorizontalHeaderLabels(translated_headers)

        # Populate data
        for row, item in enumerate(data):
            name = item.get("Name", "")
            poll_answer = item.get("Poll Answer", "")

            # Get row colors using helper function
            row_color, text_color = self._get_row_colors(
                name, poll_answer, exclude_names, theme_colors
            )

            for col, (_key, value) in enumerate(item.items()):
                # Convert value to string
                str_value = str(value) if value is not None else ""
                table_item = PollTableItem(str_value)
                table_item.setFlags(table_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                # Set text alignment - left for Name column (col 0), center for all others
                if col == 0:  # Name column
                    table_item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )
                else:  # All other columns
                    table_item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                    )

                # Apply background and text colors
                if row_color:
                    table_item.setBackground(row_color)
                if text_color:
                    table_item.setForeground(text_color)

                # Set custom data attribute to identify the row type for potential stylesheet use
                if name == "Total":
                    table_item.setData(Qt.ItemDataRole.UserRole, "total")
                elif name in exclude_names:
                    table_item.setData(Qt.ItemDataRole.UserRole, "excluded")
                elif poll_answer and poll_answer != "N/A":
                    table_item.setData(Qt.ItemDataRole.UserRole, "answered")
                else:
                    table_item.setData(Qt.ItemDataRole.UserRole, "no_answer")

                if debug_mode and col == 0:  # Only print once per row
                    if row_color:
                        print(
                            f"Debug: Applied colors bg={row_color.name()}, text={text_color.name() if text_color else 'default'} to row {row} ({name})"
                        )
                    else:
                        print(f"Debug: No color applied to row {row} ({name})")

                self.setItem(row, col, table_item)

        # Force row colors after population to ensure they're not overridden
        self.force_row_colors(data, exclude_names, theme_colors, debug_mode)

        self.setSortingEnabled(True)

        # Apply ultra-minimal column sizing AFTER all other operations
        self.apply_minimal_column_sizing(debug_mode)

        if debug_mode:
            print(
                f"Debug: Table populated with {self.rowCount()} rows and {self.columnCount()} columns"
            )

    def clear_data(self):
        """Clear all table data"""
        self.setRowCount(0)
        self.setColumnCount(0)

    def get_table_data(self) -> List[List[str]]:
        """Get all table data as list of lists for CSV export"""
        data = []

        # Add headers
        headers = []
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            headers.append(header_item.text() if header_item else f"Column {col + 1}")
        data.append(headers)

        # Add rows
        for row in range(self.rowCount()):
            row_data = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)

        return data

    def force_row_colors(
        self,
        data: List[Dict],
        exclude_names: List[str],
        theme_colors: Dict[str, str] = None,
        debug_mode: bool = False,
    ):
        """Force row background colors after table population to override theme styling"""

        for row, item in enumerate(data):
            name = item.get("Name", "")
            poll_answer = item.get("Poll Answer", "")

            # Determine row colors using theme colors
            bg_color = None
            text_color = None

            if name == "Total":
                # Total row - use default colors (handled in total row widget)
                continue
            elif name in exclude_names:
                # Excluded names
                if theme_colors:
                    bg_color = theme_colors.get("poll_row_excluded", "#e0e0e0")
                    text_color = theme_colors.get("poll_row_excluded_text", "#666666")
                else:
                    bg_color = "#e0e0e0"
                    text_color = "#666666"
            elif poll_answer and poll_answer != "N/A":
                # Has answer
                if theme_colors:
                    bg_color = theme_colors.get("poll_row_answered", "#e8f5e8")
                    text_color = theme_colors.get("poll_row_answered_text", "#2d5a2d")
                else:
                    bg_color = "#e8f5e8"
                    text_color = "#2d5a2d"
            else:
                # No answer
                if theme_colors:
                    bg_color = theme_colors.get("poll_row_no_answer", "#ffe8e8")
                    text_color = theme_colors.get("poll_row_no_answer_text", "#5a2d2d")
                else:
                    bg_color = "#ffe8e8"
                    text_color = "#5a2d2d"

            if bg_color:
                # Apply colors to all cells in this row
                for col in range(self.columnCount()):
                    table_item = self.item(row, col)
                    if table_item:
                        # Apply background color
                        table_item.setBackground(QColor(bg_color))
                        table_item.setData(
                            Qt.ItemDataRole.BackgroundRole, QColor(bg_color)
                        )

                        # Apply text color if specified
                        if text_color:
                            table_item.setForeground(QColor(text_color))
                            table_item.setData(
                                Qt.ItemDataRole.ForegroundRole, QColor(text_color)
                            )

                if debug_mode:
                    print(
                        f"Debug: Force-applied colors bg={bg_color}, text={text_color} to row {row} ({name})"
                    )

        # Apply a minimal stylesheet that doesn't interfere with our colors or fonts
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #CCCCCC;
                background-color: transparent;
            }
            QTableWidget::item {
                border: none;
                padding: 0px 3px;  /* 0px top/bottom, 3px left/right */
                margin: 0px;
                line-height: 1.0;  /* Minimal line height */
                /* Note: font settings are intentionally omitted to preserve parent font settings */
            }
            QTableWidget::item:selected {
                background-color: rgba(0, 120, 215, 0.3);
                color: inherit;
            }
        """)

        # Force row heights to be applied after data population
        self.update_row_heights()

        # Force immediate update
        self.viewport().repaint()
        self.repaint()

    def populate_test_data(self):
        """Populate table with test data to verify row coloring"""
        test_data = [
            {
                "Name": "John Doe",
                "Poll Answer": "5",
                "Join Time": "09:00:00",
                "Leave Time": "10:00:00",
                "Reconnections": "1",
            },
            {
                "Name": "Jane Smith",
                "Poll Answer": "N/A",
                "Join Time": "09:05:00",
                "Leave Time": "10:05:00",
                "Reconnections": "0",
            },
            {
                "Name": "Bob Johnson",
                "Poll Answer": "3",
                "Join Time": "09:10:00",
                "Leave Time": "10:10:00",
                "Reconnections": "2",
            },
            {
                "Name": "Alice Brown",
                "Poll Answer": "N/A",
                "Join Time": "09:15:00",
                "Leave Time": "10:15:00",
                "Reconnections": "1",
            },
            {
                "Name": "Total",
                "Poll Answer": "8",
                "Join Time": "",
                "Leave Time": "",
                "Reconnections": "",
            },
        ]

        exclude_names = ["Bob Johnson"]  # Test excluded name

        from .translations import Translations

        translations = Translations()

        self.populate_data(
            test_data, translations, True, exclude_names, False
        )  # Test with light theme

    def apply_minimal_column_sizing(self, debug_mode=False):
        """Apply ultra-minimal column sizing based on header text width"""
        header = self.horizontalHeader()
        if self.columnCount() <= 0:
            return

        if debug_mode:
            print("Debug: Applying header-text-based minimal column sizing...")

        # Disable automatic resizing completely
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # Get font metrics for measuring text
        font_metrics = self.fontMetrics()
        header_font_metrics = header.fontMetrics()

        # Calculate and set width for each column individually
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            header_text = header_item.text() if header_item else f"Col {col}"

            if col == 0:  # Name column - we'll handle this last
                continue
            else:
                # Calculate minimal width based on header text only
                text_width = header_font_metrics.boundingRect(header_text).width()
                minimal_width = text_width + 25  # Minimal padding

                # Set individual column to Fixed mode and exact width
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
                self.setColumnWidth(col, minimal_width)

                if debug_mode:
                    print(
                        f"Debug: Set '{header_text}' to {minimal_width}px (text: {text_width}px + 25px padding)"
                    )

        # Handle name column separately - calculate its minimum based on ALL content
        name_header_text = (
            self.horizontalHeaderItem(0).text()
            if self.horizontalHeaderItem(0)
            else "Name"
        )
        name_header_width = (
            header_font_metrics.boundingRect(name_header_text).width() + 30
        )

        # Check ALL name content widths to find the truly widest text
        max_name_content_width = name_header_width
        for row in range(self.rowCount()):  # Check ALL rows, not just first 10
            item = self.item(row, 0)
            if item:
                content_width = (
                    font_metrics.boundingRect(item.text()).width() + 25
                )  # Padding for readability
                max_name_content_width = max(max_name_content_width, content_width)

        # Set name column to stretch with proper minimum
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        min_name_width = max(max_name_content_width, 120)  # Reasonable minimum

        # DON'T set global minimum section size - it affects all columns!
        # Instead, ensure name column width directly and let stretch mode handle the rest
        current_name_width = self.columnWidth(0)
        if current_name_width < min_name_width:
            self.setColumnWidth(0, min_name_width)

        # Force a layout update to ensure the stretch column respects our minimum
        self.updateGeometry()

        if debug_mode:
            print(
                f"Debug: Name column minimum: {min_name_width}px (was {current_name_width}px)"
            )
            print("Debug: After manual sizing:")
            total_width = 0
            for col in range(self.columnCount()):
                col_name = (
                    self.horizontalHeaderItem(col).text()
                    if self.horizontalHeaderItem(col)
                    else f"Col {col}"
                )
                width = self.columnWidth(col)
                total_width += width
                resize_mode = header.sectionResizeMode(col)
                mode_names = {
                    0: "Interactive",
                    1: "Fixed",
                    2: "Stretch",
                    3: "ResizeToContents",
                }
                mode_name = mode_names.get(resize_mode, f"Unknown({resize_mode})")
                print(f"  {col_name}: {width}px ({mode_name})")
            print(f"Debug: Total table width needed: {total_width}px")

        # Force immediate update
        self.updateGeometry()
        self.update()

    def update_row_heights(self, debug_mode=False):
        """Update row heights based on current font size"""
        if self.rowCount() == 0:
            return

        # Calculate appropriate row height based on font metrics
        font_metrics = self.fontMetrics()
        font_height = font_metrics.height()

        # Calculate minimal row height: font height + minimal padding
        # Use at least 8px (our compact preference) but scale with font if needed
        minimal_row_height = max(
            8, font_height + 2
        )  # 2px padding (1px top + 1px bottom)

        if debug_mode:
            print(
                f"Debug: Font height: {font_height}px, Setting row height to: {minimal_row_height}px"
            )

        # Apply to all rows
        for row in range(self.rowCount()):
            self.setRowHeight(row, minimal_row_height)

        # Update the default row height for any future rows
        self.verticalHeader().setDefaultSectionSize(minimal_row_height)

        if debug_mode:
            print(
                f"Debug: Updated {self.rowCount()} rows to height {minimal_row_height}px"
            )
