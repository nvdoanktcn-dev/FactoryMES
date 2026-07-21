from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QTableWidgetItem,
)

from src.ui.dashboard.tables.dashboard_data_table import (
    DashboardDataTable,
)


class AlarmTable(DashboardDataTable):
    """
    Hiển thị Alarm, Warning và Validation gần nhất.
    """

    HEADERS = [
        "Time",
        "Level",
        "Module",
        "Code",
        "Message",
        "Status",
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
                "time",
                None,
            ),
        )

        return [
            self.format_datetime(
                created_at
            ),

            self.value_from(
                record,
                "level",
                self.value_from(
                    record,
                    "severity",
                    "INFO",
                ),
            ),

            self.value_from(
                record,
                "module",
                "",
            ),

            self.value_from(
                record,
                "code",
                "",
            ),

            self.value_from(
                record,
                "message",
                "",
            ),

            self.value_from(
                record,
                "status",
                "OPEN",
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

        if column_index != 4:
            item.setTextAlignment(
                Qt.AlignCenter
            )

        if column_index == 1:
            level = str(
                value or ""
            ).strip().upper()

            colors = {
                "INFO": "#1565C0",
                "WARNING": "#EF6C00",
                "ERROR": "#C62828",
                "CRITICAL": "#B71C1C",
            }

            item.setForeground(
                QColor(
                    colors.get(
                        level,
                        "#455A64",
                    )
                )
            )

        if column_index == 5:
            status = str(
                value or ""
            ).strip().upper()

            if status in {
                "CLOSED",
                "RESOLVED",
                "ACKNOWLEDGED",
            }:
                color = "#2E7D32"
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