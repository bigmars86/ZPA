"""Response-group sorting preserves complete rows and their colors."""

from types import SimpleNamespace

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from zpa.ui.poll_table import PollTableContainer


def test_response_groups_stay_ordered_when_sorting_and_reloading(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    container = PollTableContainer()
    rows = [
        {"Name": "Aaron red", "Poll Answer": "N/A"},
        {"Name": "Zoe gray", "Poll Answer": "N/A"},
        {"Name": "Bella green", "Poll Answer": "2"},
        {"Name": "Bob red", "Poll Answer": "N/A"},
        {"Name": "Alice gray", "Poll Answer": "5"},
        {"Name": "Chris green", "Poll Answer": "1"},
        {"Name": "Total", "Poll Answer": "3"},
    ]
    translations = SimpleNamespace(get=lambda key: key)
    excluded = ["Zoe gray", "Alice gray"]
    expected = {row["Name"]: row["Poll Answer"] for row in rows}
    table = container.main_table

    for _reload_index in range(2):
        container.populate_data(rows, translations, exclude_names=excluded)
        for column in range(2):
            for order in (Qt.SortOrder.AscendingOrder, Qt.SortOrder.DescendingOrder):
                table.sortItems(column, order)
                groups = [
                    table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                    for row in range(table.rowCount())
                ]
                assert groups == [
                    "answered",
                    "answered",
                    "excluded",
                    "excluded",
                    "no_answer",
                    "no_answer",
                ]
                for row in range(table.rowCount()):
                    name_item = table.item(row, 0)
                    answer_item = table.item(row, 1)
                    assert answer_item.text() == expected[name_item.text()]
                    assert answer_item.data(Qt.ItemDataRole.UserRole) == name_item.data(
                        Qt.ItemDataRole.UserRole
                    )
                    assert answer_item.background() == name_item.background()
    assert container.total_row.item(0, 0).text() == "Total"
    container.close()
    app.processEvents()
