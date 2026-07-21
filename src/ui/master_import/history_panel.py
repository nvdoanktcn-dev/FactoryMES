from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class HistoryPanel(QWidget):
    """
    Hiển thị lịch sử Master Import.

    Các cột:
    - Time
    - Module
    - File
    - Rows
    - Success
    - Failed
    - Duration
    - Status
    - Message
    """

    HEADERS = [
        "Time",
        "Module",
        "File",
        "Rows",
        "Success",
        "Failed",
        "Duration",
        "Status",
        "Message",
    ]

    FIELDS = [
        "time",
        "module",
        "file",
        "rows",
        "success",
        "failed",
        "duration",
        "status",
        "message",
    ]

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.table = QTableWidget(
            self
        )

        self._configure_table()
        self._build_ui()

    # ==========================================================
    # Setup
    # ==========================================================

    def _configure_table(self):
        self.table.setColumnCount(
            len(self.HEADERS)
        )

        self.table.setHorizontalHeaderLabels(
            self.HEADERS
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.verticalHeader().setVisible(
            False
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.Stretch,
        )

        header.setSectionResizeMode(
            8,
            QHeaderView.Stretch,
        )

        self.table.setSortingEnabled(
            False
        )

        self.table.setMinimumHeight(
            220
        )

    def _build_ui(self):
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.addWidget(
            self.table
        )

    # ==========================================================
    # Public API
    # ==========================================================

    def set_history(
        self,
        records,
    ):
        records = list(
            records or []
        )

        self.table.setSortingEnabled(
            False
        )

        self.table.clearContents()

        self.table.setRowCount(
            len(records)
        )

        for row_index, record in enumerate(
            records
        ):
            self._set_history_row(
                row_index=row_index,
                record=record,
            )

        self.table.resizeRowsToContents()

        self.table.setSortingEnabled(
            True
        )

    def clear_history(self):
        self.table.setSortingEnabled(
            False
        )

        self.table.clearContents()
        self.table.setRowCount(0)

        self.table.setSortingEnabled(
            True
        )

    def selected_history(self):
        selected_rows = (
            self.table
            .selectionModel()
            .selectedRows()
        )

        if not selected_rows:
            return None

        row_index = selected_rows[0].row()

        item = self.table.item(
            row_index,
            0,
        )

        if item is None:
            return None

        return item.data(
            Qt.UserRole
        )

    def selected_log_id(self):
        record = self.selected_history()

        if not record:
            return None

        value = self._get_value(
            record,
            "id",
            None,
        )

        try:
            return int(value)

        except (
            TypeError,
            ValueError,
        ):
            return None

    # ==========================================================
    # Row rendering
    # ==========================================================

    def _set_history_row(
        self,
        row_index,
        record,
    ):
        for column_index, field_name in enumerate(
            self.FIELDS
        ):
            value = self._get_value(
                record,
                field_name,
                "",
            )

            text = self._format_value(
                field_name=field_name,
                value=value,
            )

            item = QTableWidgetItem(
                text
            )

            item.setToolTip(
                text
            )

            if column_index == 0:
                item.setData(
                    Qt.UserRole,
                    record,
                )

            if field_name in {
                "rows",
                "success",
                "failed",
            }:
                item.setTextAlignment(
                    Qt.AlignCenter
                )

            if field_name == "status":
                item.setTextAlignment(
                    Qt.AlignCenter
                )

                item.setData(
                    Qt.UserRole + 1,
                    str(value or "")
                    .strip()
                    .upper(),
                )

            self.table.setItem(
                row_index,
                column_index,
                item,
            )

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _get_value(
        record,
        field_name,
        default="",
    ):
        if isinstance(
            record,
            dict,
        ):
            value = record.get(
                field_name,
                default,
            )

        else:
            value = getattr(
                record,
                field_name,
                default,
            )

        if value is None:
            return default

        return value

    @staticmethod
    def _format_value(
        field_name,
        value,
    ):
        if value is None:
            return ""

        if field_name in {
            "rows",
            "success",
            "failed",
        }:
            try:
                return str(
                    int(value)
                )

            except (
                TypeError,
                ValueError,
            ):
                return str(value)

        if field_name == "duration":
            if isinstance(
                value,
                str,
            ):
                return value

            try:
                return (
                    f"{float(value):.3f}s"
                )

            except (
                TypeError,
                ValueError,
            ):
                return str(value)

        if field_name == "status":
            return str(
                value or ""
            ).strip().upper()

        return str(value)