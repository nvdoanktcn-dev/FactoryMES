from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
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

from src.ui.controllers.production_order_controller import (
    ProductionOrderController,
)


class ProductionPage(QWidget):
    HEADERS = [
        "Work Order",
        "Product",
        "OP",
        "Operation",
        "Process",
        "Machine Type",
        "Machine",
        "Employee",
        "Shift",
        "Plan Qty",
        "Completed",
        "NG",
        "Progress",
        "Status",
        "Planned Start",
        "Planned Finish",
    ]

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName(
            "ProductionPage"
        )

        self._row_objects = []

        self.title_label = QLabel(
            "Production Order",
            self,
        )

        self.search_box = QLineEdit(
            self
        )
        self.search_box.setPlaceholderText(
            (
                "Search Work Order, Product, OP, "
                "Machine or Employee..."
            )
        )

        self.status_filter = QComboBox(
            self
        )
        self.status_filter.addItems(
            [
                "ALL",
                "PLANNED",
                "RELEASED",
                "IN_PROGRESS",
                "ON_HOLD",
                "COMPLETED",
                "CANCELLED",
            ]
        )

        self.process_filter = QComboBox(
            self
        )
        self.process_filter.addItems(
            [
                "ALL",
                "CNC",
                "ROBOT",
                "MANUAL",
                "INSPECTION",
                "OTHER",
            ]
        )

        self.btn_generate = QPushButton(
            "Generate",
            self,
        )
        self.btn_regenerate = QPushButton(
            "Regenerate",
            self,
        )
        self.btn_release = QPushButton(
            "Release",
            self,
        )
        self.btn_start = QPushButton(
            "Start",
            self,
        )
        self.btn_hold = QPushButton(
            "Hold",
            self,
        )
        self.btn_complete = QPushButton(
            "Complete",
            self,
        )
        self.btn_refresh = QPushButton(
            "Refresh",
            self,
        )

        self.total_value = QLabel(
            "0",
            self,
        )
        self.released_value = QLabel(
            "0",
            self,
        )
        self.running_value = QLabel(
            "0",
            self,
        )
        self.completed_value = QLabel(
            "0",
            self,
        )

        self.table = QTableWidget(
            self
        )

        self.status_label = QLabel(
            "",
            self,
        )

        self.controller = (
            ProductionOrderController(
                page=self
            )
        )

        self._build_ui()
        self._configure_table()
        self._connect_events()
        self._apply_style()

        self.controller.load_orders()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(
            16,
            16,
            16,
            16,
        )
        root.setSpacing(
            10
        )

        filter_layout = QHBoxLayout()

        filter_layout.addWidget(
            QLabel(
                "Search",
                self,
            )
        )
        filter_layout.addWidget(
            self.search_box,
            1,
        )
        filter_layout.addWidget(
            QLabel(
                "Status",
                self,
            )
        )
        filter_layout.addWidget(
            self.status_filter
        )
        filter_layout.addWidget(
            QLabel(
                "Process",
                self,
            )
        )
        filter_layout.addWidget(
            self.process_filter
        )

        button_layout = QHBoxLayout()

        for button in (
            self.btn_generate,
            self.btn_regenerate,
            self.btn_release,
            self.btn_start,
            self.btn_hold,
            self.btn_complete,
            self.btn_refresh,
        ):
            button_layout.addWidget(
                button
            )

        button_layout.addStretch()

        summary_layout = QGridLayout()

        summary_items = [
            (
                "Total",
                self.total_value,
                0,
            ),
            (
                "Released",
                self.released_value,
                1,
            ),
            (
                "Running",
                self.running_value,
                2,
            ),
            (
                "Completed",
                self.completed_value,
                3,
            ),
        ]

        for title, value, column in summary_items:
            box = QWidget(self)
            box.setObjectName(
                "ProductionSummaryBox"
            )

            box_layout = QVBoxLayout(
                box
            )
            box_layout.setContentsMargins(
                12,
                8,
                12,
                8,
            )

            title_label = QLabel(
                title,
                box,
            )
            title_label.setAlignment(
                Qt.AlignCenter
            )

            value.setAlignment(
                Qt.AlignCenter
            )
            value.setObjectName(
                "ProductionSummaryValue"
            )

            box_layout.addWidget(
                title_label
            )
            box_layout.addWidget(
                value
            )

            summary_layout.addWidget(
                box,
                0,
                column,
            )

        root.addWidget(
            self.title_label
        )
        root.addLayout(
            filter_layout
        )
        root.addLayout(
            button_layout
        )
        root.addLayout(
            summary_layout
        )
        root.addWidget(
            self.table,
            1,
        )
        root.addWidget(
            self.status_label
        )

    def _configure_table(self):
        self.table.setColumnCount(
            len(self.HEADERS)
        )
        self.table.setHorizontalHeaderLabels(
            self.HEADERS
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
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
        header.setStretchLastSection(
            True
        )

    def _connect_events(self):
        self.search_box.textChanged.connect(
            self.controller.load_orders
        )
        self.status_filter.currentTextChanged.connect(
            self.controller.load_orders
        )
        self.process_filter.currentTextChanged.connect(
            self.controller.load_orders
        )

        self.btn_generate.clicked.connect(
            self.controller.generate_orders
        )
        self.btn_regenerate.clicked.connect(
            self.controller
            .regenerate_selected_work_order
        )
        self.btn_release.clicked.connect(
            self.controller.release_selected
        )
        self.btn_start.clicked.connect(
            self.controller.start_selected
        )
        self.btn_hold.clicked.connect(
            self.controller.hold_selected
        )
        self.btn_complete.clicked.connect(
            self.controller.complete_selected
        )
        self.btn_refresh.clicked.connect(
            self.controller.load_orders
        )

    def _apply_style(self):
        self.title_label.setStyleSheet(
            (
                "font-size:24px;"
                "font-weight:bold;"
                "color:#263238;"
            )
        )

        self.status_label.setStyleSheet(
            "color:#546E7A;"
        )

        self.setStyleSheet(
            """
            QWidget#ProductionSummaryBox {
                background: white;
                border: 1px solid #CFD8DC;
                border-radius: 7px;
            }

            QLabel#ProductionSummaryValue {
                font-size: 22px;
                font-weight: bold;
                color: #1976D2;
            }
            """
        )

        for button in (
            self.btn_generate,
            self.btn_regenerate,
            self.btn_release,
            self.btn_start,
            self.btn_hold,
            self.btn_complete,
            self.btn_refresh,
        ):
            button.setMinimumHeight(
                32
            )

    def set_orders(
        self,
        orders,
    ):
        self._row_objects = list(
            orders or []
        )

        self.table.setRowCount(
            len(self._row_objects)
        )

        for row_index, order in enumerate(
            self._row_objects
        ):
            plan_qty = int(
                order.plan_qty or 0
            )
            completed_qty = int(
                order.completed_qty or 0
            )

            progress = (
                completed_qty
                / plan_qty
                * 100.0
                if plan_qty > 0
                else 0.0
            )

            values = [
                order.work_order_no,
                order.product_code,
                f"OP{order.operation_no}",
                order.operation_name,
                order.process_type,
                order.machine_type,
                order.machine_code,
                order.employee_code,
                order.shift,
                plan_qty,
                completed_qty,
                int(
                    order.ng_qty or 0
                ),
                f"{progress:.1f}%",
                order.status,
                self._format_datetime(
                    order.planned_start
                ),
                self._format_datetime(
                    order.planned_finish
                ),
            ]

            for column_index, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    ""
                    if value is None
                    else str(value)
                )

                if column_index in {
                    2,
                    9,
                    10,
                    11,
                    12,
                    13,
                }:
                    item.setTextAlignment(
                        Qt.AlignCenter
                    )

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.table.resizeRowsToContents()

    def selected_order(self):
        selected_rows = (
            self.table
            .selectionModel()
            .selectedRows()
        )

        if not selected_rows:
            return None

        index = selected_rows[0].row()

        if not (
            0
            <= index
            < len(self._row_objects)
        ):
            return None

        return self._row_objects[
            index
        ]

    def update_summary(
        self,
        orders,
    ):
        orders = list(
            orders or []
        )

        self.total_value.setText(
            str(
                len(orders)
            )
        )

        self.released_value.setText(
            str(
                sum(
                    1
                    for order in orders
                    if str(
                        order.status or ""
                    ).upper()
                    == "RELEASED"
                )
            )
        )

        self.running_value.setText(
            str(
                sum(
                    1
                    for order in orders
                    if str(
                        order.status or ""
                    ).upper()
                    == "IN_PROGRESS"
                )
            )
        )

        self.completed_value.setText(
            str(
                sum(
                    1
                    for order in orders
                    if str(
                        order.status or ""
                    ).upper()
                    == "COMPLETED"
                )
            )
        )

    def set_status_message(
        self,
        message,
    ):
        self.status_label.setText(
            str(
                message or ""
            )
        )

    def show_error(
        self,
        error,
    ):
        message = str(
            error
        )

        self.set_status_message(
            message
        )

        QMessageBox.warning(
            self,
            "Production Order Error",
            message,
        )

    def on_page_activated(self):
        self.controller.load_orders()

    def closeEvent(
        self,
        event,
    ):
        self.controller.close()
        super().closeEvent(
            event
        )

    @staticmethod
    def _format_datetime(
        value,
    ):
        if value is None:
            return ""

        formatter = getattr(
            value,
            "strftime",
            None,
        )

        if callable(formatter):
            return formatter(
                "%Y-%m-%d %H:%M"
            )

        return str(
            value
        )