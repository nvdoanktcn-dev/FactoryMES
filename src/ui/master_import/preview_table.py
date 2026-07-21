from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


class PreviewTable(QTableWidget):
    """
    Bảng xem trước dữ liệu import.
    """

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.setAlternatingRowColors(True)

        self.verticalHeader().setVisible(
            False
        )

        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.horizontalHeader().setStretchLastSection(
            True
        )

        self.setMinimumHeight(280)

    def set_preview_rows(
        self,
        rows,
    ):
        rows = list(rows or [])

        self.clear()

        if not rows:
            self.setRowCount(0)
            self.setColumnCount(0)
            return

        first_row = rows[0]

        if isinstance(first_row, dict):
            headers = list(
                first_row.keys()
            )
        else:
            headers = [
                f"Column {index + 1}"
                for index in range(
                    len(first_row)
                )
            ]

        self.setColumnCount(
            len(headers)
        )

        self.setHorizontalHeaderLabels(
            headers
        )

        self.setRowCount(
            len(rows)
        )

        for row_index, row in enumerate(
            rows
        ):
            if isinstance(row, dict):
                values = [
                    row.get(header, "")
                    for header in headers
                ]
            else:
                values = list(row)

            for column_index, value in enumerate(
                values
            ):
                self.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(
                        "" if value is None else str(value)
                    ),
                )

    def clear_preview(self):
        self.clear()
        self.setRowCount(0)
        self.setColumnCount(0)