from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


class DashboardTable(QTableWidget):
    """
    Table đọc dữ liệu Analytics.
    """

    def __init__(
        self,
        headers,
        parent=None,
    ):
        super().__init__(parent)

        self.headers = list(headers)

        self.setColumnCount(
            len(self.headers)
        )

        self.setHorizontalHeaderLabels(
            self.headers
        )

        self.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.setAlternatingRowColors(True)

        header = self.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        header.setStretchLastSection(True)

    def set_rows(self, rows):
        rows = list(rows or [])

        self.setSortingEnabled(False)
        self.clearContents()
        self.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for column_index in range(
                len(self.headers)
            ):
                value = (
                    row[column_index]
                    if column_index < len(row)
                    else ""
                )

                item = QTableWidgetItem(
                    self.format_value(value)
                )

                item.setTextAlignment(
                    Qt.AlignCenter
                )

                self.setItem(
                    row_index,
                    column_index,
                    item,
                )

            self.setRowHeight(
                row_index,
                30,
            )

        self.setSortingEnabled(True)

    @staticmethod
    def format_value(value):
        if value is None:
            return ""

        if isinstance(value, float):
            return f"{value:,.2f}"

        if isinstance(value, int):
            return f"{value:,}"

        return str(value)