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

from src.services.production_downtime_service import (
    ProductionDowntimeService,
)
from src.ui.controllers.production_downtime_controller import (
    ProductionDowntimeController,
)


class ProductionDowntimePage(QWidget):
    HEADERS = [
        "Downtime ID",
        "Execution ID",
        "Work Order",
        "Product",
        "OP",
        "Operation",
        "Machine",
        "Employee",
        "Shift",
        "Reason Code",
        "Reason",
        "Start Time",
        "End Time",
        "Duration (Min)",
        "Status",
        "Remark",
    ]

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName(
            "ProductionDowntimePage"
        )

        self._row_objects = []

        self.title_label = QLabel(
            "Production Downtime",
            self,
        )

        self.search_box = QLineEdit(
            self
        )
        self.search_box.setPlaceholderText(
            (
                "Search Downtime, Execution, "
                "Work Order, Product, Machine, "
                "Employee or Reason..."
            )
        )

        self.status_filter = QComboBox(
            self
        )
        self.status_filter.addItems(
            [
                "ALL",
                "OPEN",
                "CLOSED",
                "CANCELLED",
            ]
        )

        self.reason_filter = QComboBox(
            self
        )
        self.reason_filter.addItem(
            "ALL",
            None,
        )

        for code, name in (
            ProductionDowntimeService.REASONS.items()
        ):
            self.reason_filter.addItem(
                f"{name} ({code})",
                code,
            )

        self.btn_start = QPushButton(
            "Start Downtime",
            self,
        )
        self.btn_stop = QPushButton(
            "Stop Downtime",
            self,
        )
        self.btn_cancel = QPushButton(
            "Cancel",
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
        self.open_value = QLabel(
            "0",
            self,
        )
        self.closed_value = QLabel(
            "0",
            self,
        )
        self.cancelled_value = QLabel(
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
            ProductionDowntimeController(
                page=self
            )
        )

        self._build_ui()
        self._configure_table()
        self._connect_events()
        self._apply_style()

        self.controller.load_events()

    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):
        root_layout = QVBoxLayout(
            self
        )
        root_layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )
        root_layout.setSpacing(
            10
        )

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(
            8
        )

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
                "Reason",
                self,
            )
        )
        filter_layout.addWidget(
            self.reason_filter
        )

        button_layout = QHBoxLayout()
        button_layout.setSpacing(
            8
        )

        for button in (
            self.btn_start,
            self.btn_stop,
            self.btn_cancel,
            self.btn_refresh,
        ):
            button_layout.addWidget(
                button
            )

        button_layout.addStretch()

        summary_layout = QGridLayout()
        summary_layout.setSpacing(
            10
        )

        summary_items = [
            (
                "Total",
                self.total_value,
                0,
            ),
            (
                "Open",
                self.open_value,
                1,
            ),
            (
                "Closed",
                self.closed_value,
                2,
            ),
            (
                "Cancelled",
                self.cancelled_value,
                3,
            ),
        ]

        for title, value_label, column in summary_items:
            card = QWidget(
                self
            )
            card.setObjectName(
                "DowntimeSummaryCard"
            )

            card_layout = QVBoxLayout(
                card
            )
            card_layout.setContentsMargins(
                12,
                8,
                12,
                8,
            )
            card_layout.setSpacing(
                4
            )

            title_label = QLabel(
                title,
                card,
            )
            title_label.setAlignment(
                Qt.AlignCenter
            )

            value_label.setAlignment(
                Qt.AlignCenter
            )
            value_label.setObjectName(
                "DowntimeSummaryValue"
            )

            card_layout.addWidget(
                title_label
            )
            card_layout.addWidget(
                value_label
            )

            summary_layout.addWidget(
                card,
                0,
                column,
            )

        root_layout.addWidget(
            self.title_label
        )
        root_layout.addLayout(
            filter_layout
        )
        root_layout.addLayout(
            button_layout
        )
        root_layout.addLayout(
            summary_layout
        )
        root_layout.addWidget(
            self.table,
            1,
        )
        root_layout.addWidget(
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
        self.table.setSortingEnabled(
            False
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
            self.controller.load_events
        )
        self.status_filter.currentTextChanged.connect(
            self.controller.load_events
        )
        self.reason_filter.currentIndexChanged.connect(
            self.controller.load_events
        )

        self.btn_start.clicked.connect(
            self.controller.start_downtime
        )
        self.btn_stop.clicked.connect(
            self.controller.stop_selected
        )
        self.btn_cancel.clicked.connect(
            self.controller.cancel_selected
        )
        self.btn_refresh.clicked.connect(
            self.controller.refresh
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
            QWidget#DowntimeSummaryCard {
                background: white;
                border: 1px solid #CFD8DC;
                border-radius: 7px;
            }

            QLabel#DowntimeSummaryValue {
                font-size: 22px;
                font-weight: bold;
                color: #1976D2;
            }
            """
        )

        for button in (
            self.btn_start,
            self.btn_stop,
            self.btn_cancel,
            self.btn_refresh,
        ):
            button.setMinimumHeight(
                32
            )

    # ==========================================================
    # Data rendering
    # ==========================================================

    def set_events(
        self,
        rows,
    ):
        self._row_objects = [
            event
            for event, _, _, _ in rows
        ]

        self.table.setRowCount(
            len(rows)
        )

        for row_index, (
            event,
            execution,
            assignment,
            production_order,
        ) in enumerate(rows):
            values = [
                event.id,
                event.execution_id,
                (
                    production_order.work_order_no
                    if production_order
                    else ""
                ),
                (
                    production_order.product_code
                    if production_order
                    else ""
                ),
                (
                    f"OP{production_order.operation_no}"
                    if production_order
                    else ""
                ),
                (
                    production_order.operation_name
                    if production_order
                    else ""
                ),
                (
                    assignment.machine_code
                    if assignment
                    else ""
                ),
                (
                    assignment.employee_code
                    if assignment
                    else ""
                ),
                (
                    assignment.shift
                    if assignment
                    else ""
                ),
                event.reason_code,
                event.reason_name,
                self._format_datetime(
                    event.start_time
                ),
                self._format_datetime(
                    event.end_time
                ),
                self._format_number(
                    event.duration_minutes
                ),
                event.status,
                event.remark,
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
                    0,
                    1,
                    4,
                    8,
                    9,
                    13,
                    14,
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

    def selected_event(self):
        selected_rows = (
            self.table
            .selectionModel()
            .selectedRows()
        )

        if not selected_rows:
            return None

        row_index = selected_rows[0].row()

        if not (
            0
            <= row_index
            < len(self._row_objects)
        ):
            return None

        return self._row_objects[
            row_index
        ]

    def update_summary(
        self,
        events,
    ):
        events = list(
            events or []
        )

        self.total_value.setText(
            str(
                len(events)
            )
        )

        self.open_value.setText(
            str(
                sum(
                    1
                    for event in events
                    if str(
                        event.status or ""
                    ).strip().upper()
                    == "OPEN"
                )
            )
        )

        self.closed_value.setText(
            str(
                sum(
                    1
                    for event in events
                    if str(
                        event.status or ""
                    ).strip().upper()
                    == "CLOSED"
                )
            )
        )

        self.cancelled_value.setText(
            str(
                sum(
                    1
                    for event in events
                    if str(
                        event.status or ""
                    ).strip().upper()
                    == "CANCELLED"
                )
            )
        )

    # ==========================================================
    # Messages / lifecycle
    # ==========================================================

    def set_status_message(
        self,
        message,
    ):
        self.status_label.setText(
            str(
                message
                or ""
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
            "Production Downtime Error",
            message,
        )

    def on_page_activated(self):
        self.controller.load_events()

    def closeEvent(
        self,
        event,
    ):
        self.controller.close()

        super().closeEvent(
            event
        )

    # ==========================================================
    # Helpers
    # ==========================================================

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

        if callable(
            formatter
        ):
            return formatter(
                "%Y-%m-%d %H:%M:%S"
            )

        return str(
            value
        )

    @staticmethod
    def _format_number(
        value,
    ):
        if value is None:
            return "0"

        number = float(
            value
        )

        if number.is_integer():
            return str(
                int(number)
            )

        return (
            f"{number:.2f}"
            .rstrip("0")
            .rstrip(".")
        )
