from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.production_inventory_report_service import (
    ProductionInventoryReportService,
)


class ProductionInventoryReconciliationPage(QWidget):
    """Report page for production versus finished inventory."""

    TABLE_COLUMNS = (
        ("work_order_no", "Work Order"),
        ("product_code", "Product"),
        ("plan_qty", "Plan"),
        ("completed_qty", "Final OP"),
        ("ng_qty", "NG"),
        ("inventory_qty", "Inventory"),
        ("pending_inventory_qty", "Pending"),
        ("over_received_qty", "Over"),
        ("remaining_plan_qty", "Plan Remaining"),
        ("completion_percent", "Completion (%)"),
        ("inventory_percent", "Inventory (%)"),
        ("reconciliation_status", "Status"),
    )

    def __init__(
        self,
        parent=None,
        service=None,
    ) -> None:
        super().__init__(parent)
        self._owns_service = service is None
        self.service = (
            service
            or ProductionInventoryReportService()
        )
        self._current_report = None
        self._loaded_once = False

        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Custom Range",
            "Day",
            "Month",
            "Year",
        ])
        self.start_date_edit = QDateEdit()
        self.end_date_edit = QDateEdit()
        for editor in (
            self.start_date_edit,
            self.end_date_edit,
        ):
            editor.setCalendarPopup(True)
            editor.setDisplayFormat("yyyy-MM-dd")

        today = QDate.currentDate()
        self.start_date_edit.setDate(
            QDate(today.year(), today.month(), 1)
        )
        self.end_date_edit.setDate(today)

        self.work_order_edit = QLineEdit()
        self.work_order_edit.setPlaceholderText(
            "Work order..."
        )
        self.product_edit = QLineEdit()
        self.product_edit.setPlaceholderText(
            "Product code..."
        )
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "All Statuses",
            "RECONCILED",
            "PENDING_INVENTORY",
            "OVER_RECEIVED",
            "BEHIND_PLAN",
        ])

        self.load_button = QPushButton("Load Report")
        self.export_button = QPushButton("Export Excel")
        self.export_button.setEnabled(False)
        self.status_label = QLabel(
            "Select filters and load the report."
        )

        self.table = QTableWidget(
            0,
            len(self.TABLE_COLUMNS),
        )
        self.table.setHorizontalHeaderLabels([
            label
            for _, label in self.TABLE_COLUMNS
        ])
        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setStretchLastSection(
            True
        )

        self._build_ui()
        self._connect_events()
        self._apply_style()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        title = QLabel(
            "Production / Inventory Reconciliation"
        )
        title.setObjectName("ReportTitle")
        root.addWidget(title)

        filters = QGridLayout()
        filters.addWidget(QLabel("Period"), 0, 0)
        filters.addWidget(self.period_combo, 0, 1)
        filters.addWidget(QLabel("From"), 0, 2)
        filters.addWidget(self.start_date_edit, 0, 3)
        filters.addWidget(QLabel("To"), 0, 4)
        filters.addWidget(self.end_date_edit, 0, 5)
        filters.addWidget(QLabel("Work Order"), 1, 0)
        filters.addWidget(self.work_order_edit, 1, 1)
        filters.addWidget(QLabel("Product"), 1, 2)
        filters.addWidget(self.product_edit, 1, 3)
        filters.addWidget(QLabel("Status"), 1, 4)
        filters.addWidget(self.status_combo, 1, 5)
        root.addLayout(filters)

        buttons = QHBoxLayout()
        buttons.addWidget(self.load_button)
        buttons.addWidget(self.export_button)
        buttons.addStretch()
        buttons.addWidget(self.status_label)
        root.addLayout(buttons)
        root.addWidget(self.table, 1)

    def _connect_events(self) -> None:
        self.period_combo.currentTextChanged.connect(
            self._apply_period
        )
        self.load_button.clicked.connect(
            self.load_report
        )
        self.export_button.clicked.connect(
            self.export_report
        )

    def _apply_period(
        self,
        period_name,
    ) -> None:
        current = self.end_date_edit.date()
        name = str(period_name or "")
        if name == "Day":
            self.start_date_edit.setDate(current)
        elif name == "Month":
            self.start_date_edit.setDate(
                QDate(
                    current.year(),
                    current.month(),
                    1,
                )
            )
            self.end_date_edit.setDate(
                QDate(
                    current.year(),
                    current.month(),
                    current.daysInMonth(),
                )
            )
        elif name == "Year":
            self.start_date_edit.setDate(
                QDate(current.year(), 1, 1)
            )
            self.end_date_edit.setDate(
                QDate(current.year(), 12, 31)
            )

    def load_report(self) -> None:
        start_date = self._python_date(
            self.start_date_edit.date()
        )
        end_date = self._python_date(
            self.end_date_edit.date()
        )
        if end_date < start_date:
            QMessageBox.warning(
                self,
                "Invalid Period",
                "End Date cannot be earlier than Start Date.",
            )
            return

        self._set_busy(True)
        try:
            self._current_report = (
                self.service.build_report(
                    start_date,
                    end_date,
                    work_order_no=(
                        self.work_order_edit
                        .text()
                        .strip()
                        or None
                    ),
                    product_code=(
                        self.product_edit
                        .text()
                        .strip()
                        or None
                    ),
                    status=self._optional_status(),
                )
            )
            rows = self._current_report.get(
                "rows",
                [],
            )
            self._populate_table(rows)
            self._loaded_once = True
            self.export_button.setEnabled(True)
            summary = self._current_report.get(
                "summary",
                {},
            )
            self.status_label.setText(
                f"{len(rows)} order(s), "
                f"pending "
                f"{summary.get('pending_inventory_qty', 0)}, "
                f"over "
                f"{summary.get('over_received_qty', 0)}."
            )
        except Exception as error:
            self._current_report = None
            self.export_button.setEnabled(False)
            QMessageBox.critical(
                self,
                "Report Error",
                str(error),
            )
        finally:
            self._set_busy(False)

    def export_report(self) -> None:
        if self._current_report is None:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Production Inventory Reconciliation",
            "FactoryMES-production-inventory.xlsx",
            "Excel Workbook (*.xlsx)",
        )
        if not file_path:
            return
        try:
            target = self.service.export_report(
                self._current_report,
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
            f"Report saved to:\n{target}",
        )

    def _populate_table(self, rows) -> None:
        normalized = list(rows or [])
        self.table.setRowCount(len(normalized))
        for row_index, row in enumerate(
            normalized
        ):
            for column_index, (
                field,
                _,
            ) in enumerate(self.TABLE_COLUMNS):
                value = row.get(field, "")
                self.table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(
                        self._display_value(
                            field,
                            value,
                        )
                    ),
                )

    def on_page_activated(self) -> None:
        if not self._loaded_once:
            self.load_report()

    def close_resources(self) -> None:
        if self._owns_service:
            self.service.close()

    def _set_busy(self, busy) -> None:
        self.load_button.setEnabled(not busy)
        self.export_button.setEnabled(
            not busy
            and self._current_report is not None
        )

    def _optional_status(self):
        value = self.status_combo.currentText()
        return (
            None
            if value == "All Statuses"
            else value
        )

    @staticmethod
    def _python_date(value: QDate) -> date:
        return date(
            value.year(),
            value.month(),
            value.day(),
        )

    @staticmethod
    def _display_value(field, value) -> str:
        if field.endswith("_percent"):
            return f"{float(value or 0):.2f}"
        return str(
            value
            if value is not None
            else ""
        )

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QLabel#ReportTitle {
                font-size: 26px;
                font-weight: bold;
                color: #263238;
            }
            QTableWidget {
                background: #FFFFFF;
                gridline-color: #CFD8DC;
            }
            QHeaderView::section {
                background: #1976D2;
                color: #FFFFFF;
                font-weight: bold;
                padding: 7px;
            }
        """)
