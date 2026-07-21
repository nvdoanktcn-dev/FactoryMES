from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QTableWidgetItem,
)

from src.ui.dashboard.tables.dashboard_data_table import (
    DashboardDataTable,
)


class RecentProductionTable(
    DashboardDataTable
):
    """
    Hiển thị Production Log gần nhất.
    """

    HEADERS = [
        "Time",
        "Work Order",
        "Product",
        "OP",
        "Machine",
        "Employee",
        "OK",
        "NG",
        "Yield",
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
        start_time = self.value_from(
            record,
            "start_time",
            None,
        )

        ok_qty = self.to_int(
            self.value_from(
                record,
                "ok_qty",
                0,
            )
        )

        ng_qty = self.to_int(
            self.value_from(
                record,
                "ng_qty",
                0,
            )
        )

        total_qty = ok_qty + ng_qty

        yield_percent = (
            ok_qty / total_qty * 100
            if total_qty > 0
            else 0.0
        )

        return [
            self.format_datetime(
                start_time
            ),

            self.value_from(
                record,
                "work_order_no",
                "",
            ),

            self.value_from(
                record,
                "product_code",
                "",
            ),

            self.value_from(
                record,
                "op_no",
                "",
            ),

            self.value_from(
                record,
                "machine_code",
                "",
            ),

            self.value_from(
                record,
                "employee_code",
                "",
            ),

            ok_qty,
            ng_qty,
            f"{yield_percent:.2f}%",

            self.value_from(
                record,
                "status",
                "",
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

        if column_index in {
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
        }:
            item.setTextAlignment(
                Qt.AlignCenter
            )

        # NG
        if column_index == 7:
            ng_qty = self.to_int(value)

            if ng_qty > 0:
                item.setForeground(
                    QColor("#C62828")
                )

        # Yield
        if column_index == 8:
            yield_percent = self.to_float(
                str(value).replace(
                    "%",
                    "",
                )
            )

            if yield_percent >= 98:
                color = "#2E7D32"

            elif yield_percent >= 95:
                color = "#EF6C00"

            else:
                color = "#C62828"

            item.setForeground(
                QColor(color)
            )

        # Status
        if column_index == 9:
            status = str(
                value or ""
            ).strip().upper()

            if status in {
                "COMPLETED",
                "CLOSED",
            }:
                color = "#2E7D32"

            elif status in {
                "RUNNING",
                "STARTED",
            }:
                color = "#1565C0"

            elif status in {
                "ERROR",
                "CANCELLED",
            }:
                color = "#C62828"

            else:
                color = "#455A64"

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