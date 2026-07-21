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

from src.services.production_ng_service import (
    ProductionNGService,
)
from src.ui.controllers.production_ng_controller import (
    ProductionNGController,
)


class ProductionNGPage(QWidget):
    HEADERS = [
        "NG ID",
        "Execution ID",
        "Work Order",
        "Product",
        "OP",
        "Operation",
        "Machine",
        "Employee",
        "Shift",
        "NG Type",
        "Reason Code",
        "Reason",
        "Quantity",
        "Recorded At",
        "Status",
        "Remark",
    ]

    TYPE_LABELS = {
        ProductionNGService.TYPE_PROCESSING: (
            "Gia công NG"
        ),
        ProductionNGService.TYPE_BLANK: (
            "Phôi NG"
        ),
    }

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName(
            "ProductionNGPage"
        )

        self._row_objects = []

        self.title_label = QLabel(
            "Production NG",
            self,
        )

        self.search_box = QLineEdit(
            self
        )
        self.search_box.setPlaceholderText(
            (
                "Search NG, Execution, Work Order, "
                "Product, OP, Machine, Employee "
                "or Reason..."
            )
        )

        self.status_filter = QComboBox(
            self
        )
        self.status_filter.addItems(
            [
                "ALL",
                "ACTIVE",
                "CANCELLED",
            ]
        )

        self.type_filter = QComboBox(
            self
        )
        self.type_filter.addItem(
            "ALL",
            None,
        )
        self.type_filter.addItem(
            "Gia công NG (PROCESSING)",
            ProductionNGService.TYPE_PROCESSING,
        )
        self.type_filter.addItem(
            "Phôi NG (BLANK)",
            ProductionNGService.TYPE_BLANK,
        )

        self.reason_filter = QComboBox(
            self
        )
        self.reason_filter.addItem(
            "ALL",
            None,
        )

        for code, name in (
            ProductionNGService.REASONS.items()
        ):
            self.reason_filter.addItem(
                f"{name} ({code})",
                code,
            )

        self.btn_add = QPushButton(
            "Add NG",
            self,
        )
        self.btn_edit = QPushButton(
            "Edit",
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

        self.total_ng_value = QLabel(
            "0",
            self,
        )
        self.processing_ng_value = QLabel(
            "0",
            self,
        )
        self.blank_ng_value = QLabel(
            "0",
            self,
        )
        self.active_records_value = QLabel(
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
            ProductionNGController(
                page=self
            )
        )

        self._build_ui()
        self._configure_table()
        self._connect_events()
        self._apply_style()

        self.controller.load_records()

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
                "NG Type",
                self,
            )
        )
        filter_layout.addWidget(
            self.type_filter
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
            self.btn_add,
            self.btn_edit,
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
                "Total NG",
                self.total_ng_value,
                0,
            ),
            (
                "Processing NG",
                self.processing_ng_value,
                1,
            ),
            (
                "Blank NG",
                self.blank_ng_value,
                2,
            ),
            (
                "Active Records",
                self.active_records_value,
                3,
            ),
        ]

        for title, value_label, column in summary_items:
            card = QWidget(
                self
            )
            card.setObjectName(
                "ProductionNGSummaryCard"
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
                "ProductionNGSummaryValue"
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
            self.controller.load_records
        )
        self.status_filter.currentTextChanged.connect(
            self.controller.load_records
        )
        self.type_filter.currentIndexChanged.connect(
            self.controller.load_records
        )
        self.reason_filter.currentIndexChanged.connect(
            self.controller.load_records
        )

        self.btn_add.clicked.connect(
            self.controller.add_record
        )
        self.btn_edit.clicked.connect(
            self.controller.edit_selected
        )
        self.btn_cancel.clicked.connect(
            self.controller.cancel_selected
        )
        self.btn_refresh.clicked.connect(
            self.controller.refresh
        )

        self.table.doubleClicked.connect(
            self.controller.edit_selected
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
            QWidget#ProductionNGSummaryCard {
                background: white;
                border: 1px solid #CFD8DC;
                border-radius: 7px;
            }

            QLabel#ProductionNGSummaryValue {
                font-size: 22px;
                font-weight: bold;
                color: #1976D2;
            }
            """
        )

        for button in (
            self.btn_add,
            self.btn_edit,
            self.btn_cancel,
            self.btn_refresh,
        ):
            button.setMinimumHeight(
                32
            )

    # ==========================================================
    # Data rendering
    # ==========================================================

    def set_records(
        self,
        rows,
    ):
        self._row_objects = [
            record
            for record, _, _, _ in rows
        ]

        self.table.setRowCount(
            len(rows)
        )

        for row_index, (
            record,
            execution,
            assignment,
            production_order,
        ) in enumerate(rows):
            ng_type_label = self.TYPE_LABELS.get(
                str(
                    record.ng_type
                    or ""
                ).strip().upper(),
                str(
                    record.ng_type
                    or ""
                ),
            )

            values = [
                record.id,
                record.execution_id,
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
                    record.employee_code
                    or (
                        assignment.employee_code
                        if assignment
                        else ""
                    )
                ),
                (
                    assignment.shift
                    if assignment
                    else ""
                ),
                (
                    f"{ng_type_label} "
                    f"({record.ng_type})"
                ),
                record.reason_code,
                record.reason_name,
                int(
                    record.quantity
                    or 0
                ),
                self._format_datetime(
                    record.recorded_at
                ),
                record.status,
                record.remark,
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
                    10,
                    12,
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

    def selected_record(self):
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
        records,
    ):
        records = list(
            records or []
        )

        active_records = [
            record
            for record in records
            if str(
                record.status
                or ""
            ).strip().upper()
            == "ACTIVE"
        ]

        total_ng = sum(
            int(
                record.quantity
                or 0
            )
            for record in active_records
        )

        processing_ng = sum(
            int(
                record.quantity
                or 0
            )
            for record in active_records
            if str(
                record.ng_type
                or ""
            ).strip().upper()
            == ProductionNGService.TYPE_PROCESSING
        )

        blank_ng = sum(
            int(
                record.quantity
                or 0
            )
            for record in active_records
            if str(
                record.ng_type
                or ""
            ).strip().upper()
            == ProductionNGService.TYPE_BLANK
        )

        self.total_ng_value.setText(
            str(
                total_ng
            )
        )

        self.processing_ng_value.setText(
            str(
                processing_ng
            )
        )

        self.blank_ng_value.setText(
            str(
                blank_ng
            )
        )

        self.active_records_value.setText(
            str(
                len(active_records)
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
            "Production NG Error",
            message,
        )

    def on_page_activated(self):
        self.controller.load_records()

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
