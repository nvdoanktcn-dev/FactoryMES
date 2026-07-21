from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


class DashboardDataTable(QTableWidget):
    """
    Table nền dùng chung cho Dashboard.

    Chức năng:
    - Read-only
    - Chọn theo dòng
    - Alternating row colors
    - Auto resize cột
    - Empty state
    - Hỗ trợ style từng cell
    """

    def __init__(
        self,
        headers,
        parent=None,
    ):
        super().__init__(parent)

        self.headers = list(
            headers or []
        )

        if not self.headers:
            raise ValueError(
                "DashboardDataTable headers "
                "are required."
            )

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
        self.setSortingEnabled(False)

        self.verticalHeader().setVisible(False)

        header = self.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        header.setStretchLastSection(True)

        self.setMinimumHeight(230)

        self.setStyleSheet("""
            QTableWidget {
                background: #FFFFFF;
                alternate-background-color: #F7F9FA;
                border: 1px solid #CFD8DC;
                gridline-color: #ECEFF1;
            }

            QHeaderView::section {
                background: #ECEFF1;
                color: #37474F;
                font-weight: bold;
                padding: 6px;
                border: none;
                border-right: 1px solid #CFD8DC;
                border-bottom: 1px solid #CFD8DC;
            }

            QTableWidget::item {
                padding: 4px;
            }

            QTableWidget::item:selected {
                background: #BBDEFB;
                color: #102027;
            }
        """)

    # ==========================================================
    # Public API
    # ==========================================================

    def set_records(
        self,
        records,
    ):
        records = list(
            records or []
        )

        self.setSortingEnabled(False)
        self.clearContents()
        self.setRowCount(
            len(records)
        )

        for row_index, record in enumerate(
            records
        ):
            values = list(
                self.record_to_row(record)
            )

            for column_index in range(
                len(self.headers)
            ):
                value = (
                    values[column_index]
                    if column_index < len(values)
                    else ""
                )

                item = self.create_item(
                    record=record,
                    column_index=column_index,
                    value=value,
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

    def clear_records(self):
        self.clearContents()
        self.setRowCount(0)

    def selected_record_index(self):
        selected_rows = (
            self.selectionModel()
            .selectedRows()
        )

        if not selected_rows:
            return None

        return selected_rows[0].row()

    # ==========================================================
    # Extension points
    # ==========================================================

    def record_to_row(
        self,
        record,
    ):
        raise NotImplementedError

    def create_item(
        self,
        record,
        column_index,
        value,
    ):
        item = QTableWidgetItem(
            self.format_value(value)
        )

        item.setFlags(
            item.flags()
            & ~Qt.ItemIsEditable
        )

        return item

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def format_value(value):
        if value is None:
            return ""

        if isinstance(value, float):
            return f"{value:,.2f}"

        if isinstance(value, int):
            return f"{value:,}"

        return str(value)

    @staticmethod
    def value_from(
        source,
        field_name,
        default="",
    ):
        if source is None:
            return default

        if isinstance(source, dict):
            value = source.get(
                field_name,
                default,
            )

        else:
            value = getattr(
                source,
                field_name,
                default,
            )

        return (
            default
            if value is None
            else value
        )

    @staticmethod
    def to_int(value):
        try:
            return int(
                float(value or 0)
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0

    @staticmethod
    def to_float(value):
        try:
            return float(
                value or 0
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0.0