from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QTableWidgetItem,
)

from src.ui.dashboard.tables.dashboard_data_table import (
    DashboardDataTable,
)


class ImportHistoryTable(
    DashboardDataTable
):
    """
    Hiển thị lịch sử import gần nhất.
    """

    HEADERS = [
        "Time",
        "Module",
        "Filename",
        "Total",
        "Created",
        "Updated",
        "Invalid",
        "Result",
        "Operator",
    ]

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(
            headers=self.HEADERS,
            parent=parent,
        )

    def record_to_row(
        self,
        record,
    ):
        created_at = self.value_from(
            record,
            "created_at",
            self.value_from(
                record,
                "import_time",
                None,
            ),
        )

        invalid = self.to_int(
            self.value_from(
                record,
                "invalid",
                self.value_from(
                    record,
                    "invalid_count",
                    0,
                ),
            )
        )

        result = self.value_from(
            record,
            "result",
            self.value_from(
                record,
                "status",
                (
                    "SUCCESS"
                    if invalid == 0
                    else "PARTIAL"
                ),
            ),
        )

        return [
            self.format_datetime(
                created_at
            ),

            self.value_from(
                record,
                "module",
                self.value_from(
                    record,
                    "entity_name",
                    "",
                ),
            ),

            self.value_from(
                record,
                "filename",
                self.value_from(
                    record,
                    "file_name",
                    "",
                ),
            ),

            self.to_int(
                self.value_from(
                    record,
                    "total",
                    self.value_from(
                        record,
                        "total_count",
                        0,
                    ),
                )
            ),

            self.to_int(
                self.value_from(
                    record,
                    "created",
                    self.value_from(
                        record,
                        "created_count",
                        0,
                    ),
                )
            ),

            self.to_int(
                self.value_from(
                    record,
                    "updated",
                    self.value_from(
                        record,
                        "updated_count",
                        0,
                    ),
                )
            ),

            invalid,

            result,

            self.value_from(
                record,
                "operator",
                self.value_from(
                    record,
                    "created_by",
                    "",
                ),
            ),
        ]

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

        if column_index != 2:
            item.setTextAlignment(
                Qt.AlignCenter
            )

        if column_index == 6:
            invalid = self.to_int(value)

            if invalid > 0:
                item.setForeground(
                    QColor("#C62828")
                )

        if column_index == 7:
            status = str(
                value or ""
            ).strip().upper()

            if status in {
                "SUCCESS",
                "COMPLETED",
                "OK",
            }:
                color = "#2E7D32"

            elif status in {
                "PARTIAL",
                "WARNING",
            }:
                color = "#EF6C00"

            else:
                color = "#C62828"

            item.setForeground(
                QColor(color)
            )

        return item

    @staticmethod
    def format_datetime(value):
        if value is None:
            return ""

        if isinstance(value, datetime):
            return value.strftime(
                "%Y-%m-%d %H:%M"
            )

        return str(value)