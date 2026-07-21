from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)


DEFAULT_TABLE_COLUMNS = (
    ("group_label", "Nhóm"),
    ("execution_count", "Executions"),
    ("planned_minutes", "Planned (Min)"),
    ("runtime_minutes", "Runtime (Min)"),
    ("downtime_minutes", "Downtime (Min)"),
    ("ok_quantity", "OK"),
    ("ng_quantity", "NG"),
    ("total_quantity", "Total"),
    ("availability", "Availability (%)"),
    ("performance", "Performance (%)"),
    ("quality", "Quality (%)"),
    ("oee", "OEE (%)"),
)


class OEEBreakdownPanel(QTabWidget):
    """
    Panel quản lý các bảng breakdown của OEE Dashboard.
    """

    def __init__(
        self,
        columns: Sequence[tuple[str, str]]
        = DEFAULT_TABLE_COLUMNS,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.columns = tuple(columns)

        self.machine_table = self._create_table()
        self.employee_table = self._create_table()
        self.work_order_table = self._create_table()
        self.product_table = self._create_table()
        self.operation_table = self._create_table()

        self.addTab(
            self.machine_table,
            "Theo máy",
        )
        self.addTab(
            self.employee_table,
            "Theo nhân viên",
        )
        self.addTab(
            self.work_order_table,
            "Theo Work Order",
        )
        self.addTab(
            self.product_table,
            "Theo sản phẩm",
        )
        self.addTab(
            self.operation_table,
            "Theo OP",
        )

    def _create_table(self) -> QTableWidget:
        table = QTableWidget(
            0,
            len(self.columns),
        )

        table.setHorizontalHeaderLabels(
            [
                title
                for _, title in self.columns
            ]
        )

        table.setAlternatingRowColors(True)

        table.setSelectionBehavior(
            QAbstractItemView
            .SelectionBehavior
            .SelectRows
        )

        table.setSelectionMode(
            QAbstractItemView
            .SelectionMode
            .SingleSelection
        )

        table.setEditTriggers(
            QAbstractItemView
            .EditTrigger
            .NoEditTriggers
        )

        table.setSortingEnabled(True)
        table.verticalHeader().setVisible(False)

        header = table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView
            .ResizeMode
            .ResizeToContents
        )

        header.setSectionResizeMode(
            0,
            QHeaderView
            .ResizeMode
            .Stretch,
        )

        return table

    def set_data(
        self,
        *,
        by_machine: Iterable[Mapping[str, Any]],
        by_employee: Iterable[Mapping[str, Any]],
        by_work_order: Iterable[Mapping[str, Any]],
        by_product: Iterable[Mapping[str, Any]],
        by_operation: Iterable[Mapping[str, Any]],
    ) -> None:
        self.populate_table(
            self.machine_table,
            by_machine,
        )
        self.populate_table(
            self.employee_table,
            by_employee,
        )
        self.populate_table(
            self.work_order_table,
            by_work_order,
        )
        self.populate_table(
            self.product_table,
            by_product,
        )
        self.populate_table(
            self.operation_table,
            by_operation,
        )

    def populate_table(
        self,
        table: QTableWidget,
        rows: Iterable[Mapping[str, Any]],
    ) -> None:
        normalized_rows = list(rows or [])

        table.setSortingEnabled(False)
        table.clearContents()
        table.setRowCount(
            len(normalized_rows)
        )

        for row_index, raw_row in enumerate(
            normalized_rows
        ):
            row = self._as_mapping(raw_row)

            for column_index, (
                field_name,
                _,
            ) in enumerate(self.columns):
                value = row.get(
                    field_name,
                    "",
                )

                item = QTableWidgetItem(
                    self._format_cell_value(
                        field_name,
                        value,
                    )
                )

                if field_name != "group_label":
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight
                        | Qt.AlignmentFlag.AlignVCenter
                    )

                if field_name == "oee":
                    self._apply_oee_cell_style(
                        item,
                        self._number(value),
                    )

                table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        table.setSortingEnabled(True)

    def clear(self) -> None:
        for table in (
            self.machine_table,
            self.employee_table,
            self.work_order_table,
            self.product_table,
            self.operation_table,
        ):
            table.clearContents()
            table.setRowCount(0)

    @staticmethod
    def _as_mapping(
        value: Any,
    ) -> Mapping[str, Any]:
        if isinstance(value, Mapping):
            return value

        if hasattr(value, "__dict__"):
            return vars(value)

        return {}

    @staticmethod
    def _format_cell_value(
        field_name: str,
        value: Any,
    ) -> str:
        if value is None:
            return ""

        if field_name in {
            "execution_count",
            "ok_quantity",
            "ng_quantity",
            "total_quantity",
        }:
            try:
                return (
                    f"{int(round(float(value))):,}"
                )
            except (
                TypeError,
                ValueError,
            ):
                return str(value)

        if field_name in {
            "planned_minutes",
            "runtime_minutes",
            "downtime_minutes",
            "availability",
            "performance",
            "quality",
            "oee",
        }:
            try:
                return f"{float(value):,.2f}"
            except (
                TypeError,
                ValueError,
            ):
                return str(value)

        return str(value)

    @staticmethod
    def _apply_oee_cell_style(
        item: QTableWidgetItem,
        oee: float,
    ) -> None:
        if oee >= 85:
            item.setBackground(
                QColor("#D1FAE5")
            )
        elif oee >= 60:
            item.setBackground(
                QColor("#FEF3C7")
            )
        else:
            item.setBackground(
                QColor("#FEE2E2")
            )

    @staticmethod
    def _number(
        value: Any,
    ) -> float:
        try:
            return float(value or 0)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0