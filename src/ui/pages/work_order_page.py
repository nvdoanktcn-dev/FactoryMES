from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
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

from src.ui.controllers.work_order_controller import WorkOrderController


class WorkOrderPage(QWidget):
    HEADERS = [
        "Work Order No",
        "Product Code",
        "Plan Qty",
        "Start Date",
        "Due Date",
        "Priority",
        "Status",
        "Remark",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WorkOrderPage")
        self._row_objects = []

        self.title_label = QLabel("Work Order Management", self)
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText(
            "Search Work Order, Product, Status or Remark..."
        )

        self.status_filter = QComboBox(self)
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

        self.priority_filter = QComboBox(self)
        self.priority_filter.addItems(["ALL", "LOW", "NORMAL", "HIGH", "URGENT"])

        self.btn_add = QPushButton("Add", self)
        self.btn_edit = QPushButton("Edit", self)
        self.btn_release = QPushButton("Release", self)
        self.btn_start = QPushButton("Start", self)
        self.btn_complete = QPushButton("Complete", self)
        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_refresh = QPushButton("Refresh", self)

        self.table = QTableWidget(self)
        self.status_label = QLabel("", self)
        self.controller = WorkOrderController(page=self)

        self._build_ui()
        self._configure_table()
        self._connect_events()
        self._apply_style()
        self.controller.load_work_orders()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(10)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search", self))
        filter_layout.addWidget(self.search_box, 1)
        filter_layout.addWidget(QLabel("Status", self))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(QLabel("Priority", self))
        filter_layout.addWidget(self.priority_filter)

        button_layout = QHBoxLayout()
        for button in (
            self.btn_add,
            self.btn_edit,
            self.btn_release,
            self.btn_start,
            self.btn_complete,
            self.btn_cancel,
            self.btn_refresh,
        ):
            button_layout.addWidget(button)
        button_layout.addStretch()

        root_layout.addWidget(self.title_label)
        root_layout.addLayout(filter_layout)
        root_layout.addLayout(button_layout)
        root_layout.addWidget(self.table, 1)
        root_layout.addWidget(self.status_label)

    def _configure_table(self):
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

    def _connect_events(self):
        self.search_box.textChanged.connect(self.controller.load_work_orders)
        self.status_filter.currentTextChanged.connect(self.controller.load_work_orders)
        self.priority_filter.currentTextChanged.connect(self.controller.load_work_orders)
        self.btn_add.clicked.connect(self.controller.add_work_order)
        self.btn_edit.clicked.connect(self.controller.edit_selected_work_order)
        self.btn_release.clicked.connect(self.controller.release_selected_work_order)
        self.btn_start.clicked.connect(self.controller.start_selected_work_order)
        self.btn_complete.clicked.connect(self.controller.complete_selected_work_order)
        self.btn_cancel.clicked.connect(self.controller.cancel_selected_work_order)
        self.btn_refresh.clicked.connect(self.controller.load_work_orders)
        self.table.doubleClicked.connect(self.controller.edit_selected_work_order)

    def _apply_style(self):
        self.title_label.setStyleSheet(
            "font-size:24px;font-weight:bold;color:#263238;"
        )
        self.status_label.setStyleSheet("color:#546E7A;")
        for button in (
            self.btn_add,
            self.btn_edit,
            self.btn_release,
            self.btn_start,
            self.btn_complete,
            self.btn_cancel,
            self.btn_refresh,
        ):
            button.setMinimumHeight(32)

    def set_work_orders(self, work_orders):
        self._row_objects = list(work_orders or [])
        self.table.setRowCount(len(self._row_objects))

        for row_index, work_order in enumerate(self._row_objects):
            values = [
                work_order.work_order_no,
                work_order.product_code,
                work_order.plan_qty,
                work_order.start_date,
                work_order.due_date,
                work_order.priority,
                work_order.status,
                work_order.remark,
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem("" if value is None else str(value))
                if column_index in {0, 1, 2, 3, 4, 5, 6}:
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_index, column_index, item)

        self.table.resizeRowsToContents()

    def selected_work_order(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None

        row_index = selected_rows[0].row()
        if 0 <= row_index < len(self._row_objects):
            return self._row_objects[row_index]
        return None

    def set_status_message(self, message):
        self.status_label.setText(str(message or ""))

    def show_error(self, error):
        message = str(error)
        self.set_status_message(message)
        QMessageBox.warning(self, "Work Order Error", message)

    def on_page_activated(self):
        self.controller.load_work_orders()

    def closeEvent(self, event):
        self.controller.close()
        super().closeEvent(event)
