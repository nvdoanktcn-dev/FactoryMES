from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class ProductionInventoryReconciliationDetailDialog(
    QDialog
):
    DAILY_COLUMNS = (
        ("date", "Date"),
        ("final_op_qty", "Final OP"),
        ("ng_qty", "NG"),
        ("inventory_qty", "Inventory"),
        ("daily_variance", "Daily Variance"),
        (
            "cumulative_production",
            "Cumulative Production",
        ),
        (
            "cumulative_inventory",
            "Cumulative Inventory",
        ),
        ("cumulative_pending", "Pending"),
        ("cumulative_over", "Over"),
    )
    PRODUCTION_COLUMNS = (
        ("production_log_id", "Log ID"),
        ("start_time", "Start"),
        ("finish_time", "Finish"),
        ("operation", "OP"),
        ("is_final_operation", "Final OP"),
        ("machine_code", "Machine"),
        ("employee_code", "Employee"),
        ("shift", "Shift"),
        ("ok_qty", "OK"),
        ("ng_qty", "NG"),
        ("run_time_hours", "Runtime (H)"),
        ("downtime_min", "Downtime"),
        ("status", "Status"),
    )
    INVENTORY_COLUMNS = (
        ("inventory_id", "Inventory ID"),
        ("inventory_date", "Date"),
        ("qty", "Qty"),
        ("import_log_id", "Import Log"),
        ("import_file", "Import File"),
        ("import_time", "Import Time"),
        ("import_status", "Import Status"),
    )

    def __init__(
        self,
        parent=None,
        *,
        detail,
        service,
    ):
        super().__init__(parent)
        self.detail = dict(detail or {})
        self.service = service
        self.setWindowTitle(
            "Production / Inventory Detail"
        )
        self.resize(1450, 760)

        self.summary_label = QLabel()
        self.tabs = QTabWidget()
        self.daily_table = self._create_table(
            self.DAILY_COLUMNS
        )
        self.production_table = self._create_table(
            self.PRODUCTION_COLUMNS
        )
        self.inventory_table = self._create_table(
            self.INVENTORY_COLUMNS
        )
        self.export_button = QPushButton(
            "Export Detail Excel"
        )
        self.close_button = QPushButton("Close")

        self._build_ui()
        self._connect_events()
        self.load_detail()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.addWidget(self.summary_label)
        self.tabs.addTab(
            self._table_page(self.daily_table),
            "Daily",
        )
        self.tabs.addTab(
            self._table_page(self.production_table),
            "Production Logs",
        )
        self.tabs.addTab(
            self._table_page(self.inventory_table),
            "Inventory Receipts",
        )
        root.addWidget(self.tabs, 1)

        buttons = QHBoxLayout()
        buttons.addWidget(self.export_button)
        buttons.addStretch()
        buttons.addWidget(self.close_button)
        root.addLayout(buttons)

    @staticmethod
    def _table_page(table):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(table)
        return page

    @staticmethod
    def _create_table(columns):
        table = QTableWidget(0, len(columns))
        table.setHorizontalHeaderLabels([
            label
            for _, label in columns
        ])
        table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        table.horizontalHeader().setStretchLastSection(
            True
        )
        return table

    def _connect_events(self):
        self.export_button.clicked.connect(
            self.export_detail
        )
        self.close_button.clicked.connect(self.accept)

    def load_detail(self):
        row = dict(
            self.detail.get("selected_row", {})
            or {}
        )
        self.summary_label.setText(
            (
                f"Work Order: "
                f"{row.get('work_order_no', '')}  |  "
                f"Product: "
                f"{row.get('product_code', '')}  |  "
                f"Plan: {row.get('plan_qty', 0)}  |  "
                f"Final OP: "
                f"{row.get('completed_qty', 0)}  |  "
                f"NG: {row.get('ng_qty', 0)}  |  "
                f"Inventory: "
                f"{row.get('inventory_qty', 0)}  |  "
                f"Status: "
                f"{row.get('reconciliation_status', '')}"
            )
        )
        self.summary_label.setStyleSheet(
            "font-size:14px;font-weight:bold;"
        )
        self._populate(
            self.daily_table,
            self.DAILY_COLUMNS,
            self.detail.get("daily_detail", []),
        )
        self._populate(
            self.production_table,
            self.PRODUCTION_COLUMNS,
            self.detail.get(
                "production_detail", []
            ),
        )
        self._populate(
            self.inventory_table,
            self.INVENTORY_COLUMNS,
            self.detail.get(
                "inventory_receipts", []
            ),
        )

    @staticmethod
    def _populate(table, columns, rows):
        normalized = list(rows or [])
        table.setRowCount(len(normalized))
        for row_index, row in enumerate(normalized):
            for column_index, (field, _) in enumerate(
                columns
            ):
                value = row.get(field, "")
                if isinstance(value, bool):
                    value = "YES" if value else "NO"
                item = QTableWidgetItem(
                    "" if value is None else str(value)
                )
                if isinstance(value, (int, float)):
                    item.setTextAlignment(Qt.AlignCenter)
                table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    def export_detail(self):
        row = dict(
            self.detail.get("selected_row", {})
            or {}
        )
        default_name = (
            "FactoryMES-reconciliation-detail-"
            f"{row.get('work_order_no', 'work-order')}.xlsx"
        )
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Reconciliation Detail",
            default_name,
            "Excel Workbook (*.xlsx)",
        )
        if not file_path:
            return
        try:
            target = self.service.export_detail(
                self.detail,
                file_path,
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Export Error",
                str(error),
            )
            return
        QMessageBox.information(
            self,
            "Export Complete",
            f"Detail saved to:\n{target}",
        )
