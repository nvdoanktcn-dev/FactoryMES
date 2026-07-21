from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from src.ui.controllers.routing_controller import RoutingController


class RoutingPage(QWidget):
    HEADERS = [
        "Product Code", "OP", "Operation Name", "Process Type",
        "Machine Type", "Cycle Time (Sec)", "Output (PCS/H)",
        "Operators", "Status", "Remark",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RoutingPage")
        self._row_objects = []

        self.title_label = QLabel("Routing Management", self)
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("Search Product, OP, operation, process or machine type...")

        self.process_filter = QComboBox(self)
        self.process_filter.addItems(["ALL", "CNC", "ROBOT", "MANUAL", "INSPECTION", "OTHER"])
        self.status_filter = QComboBox(self)
        self.status_filter.addItems(["ALL", "ACTIVE", "INACTIVE"])

        self.btn_add = QPushButton("Add", self)
        self.btn_edit = QPushButton("Edit", self)
        self.btn_inactive = QPushButton("Set Inactive", self)
        self.btn_refresh = QPushButton("Refresh", self)

        self.table = QTableWidget(self)
        self.status_label = QLabel("", self)
        self.controller = RoutingController(page=self)

        self._build_ui()
        self._configure_table()
        self._connect_events()
        self._apply_style()
        self.controller.load_routings()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Search", self))
        filters.addWidget(self.search_box, 1)
        filters.addWidget(QLabel("Process", self))
        filters.addWidget(self.process_filter)
        filters.addWidget(QLabel("Status", self))
        filters.addWidget(self.status_filter)

        buttons = QHBoxLayout()
        buttons.addWidget(self.btn_add)
        buttons.addWidget(self.btn_edit)
        buttons.addWidget(self.btn_inactive)
        buttons.addWidget(self.btn_refresh)
        buttons.addStretch()

        root.addWidget(self.title_label)
        root.addLayout(filters)
        root.addLayout(buttons)
        root.addWidget(self.table, 1)
        root.addWidget(self.status_label)

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
        self.search_box.textChanged.connect(self.controller.load_routings)
        self.process_filter.currentTextChanged.connect(self.controller.load_routings)
        self.status_filter.currentTextChanged.connect(self.controller.load_routings)
        self.btn_add.clicked.connect(self.controller.add_routing)
        self.btn_edit.clicked.connect(self.controller.edit_selected_routing)
        self.btn_inactive.clicked.connect(self.controller.inactivate_selected_routing)
        self.btn_refresh.clicked.connect(self.controller.load_routings)
        self.table.doubleClicked.connect(self.controller.edit_selected_routing)

    def _apply_style(self):
        self.title_label.setStyleSheet("font-size:24px;font-weight:bold;color:#263238;")
        self.status_label.setStyleSheet("color:#546E7A;")
        for button in (self.btn_add, self.btn_edit, self.btn_inactive, self.btn_refresh):
            button.setMinimumHeight(32)

    def set_routings(self, routings):
        self._row_objects = list(routings or [])
        self.table.setRowCount(len(self._row_objects))

        for row_index, routing in enumerate(self._row_objects):
            values = [
                routing.product_code,
                f"OP{routing.operation_no}",
                routing.operation_name,
                routing.process_type,
                routing.machine_type,
                self._format_number(routing.standard_cycle_time_sec),
                self._format_number(routing.standard_output_pcs_hour),
                self._format_number(routing.standard_operator_count),
                routing.status,
                routing.remark,
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem("" if value is None else str(value))
                if column_index in {1, 5, 6, 7}:
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_index, column_index, item)

        self.table.resizeRowsToContents()

    def selected_routing(self):
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
        QMessageBox.warning(self, "Routing Error", message)

    def on_page_activated(self):
        self.controller.load_routings()

    def closeEvent(self, event):
        self.controller.close()
        super().closeEvent(event)

    @staticmethod
    def _format_number(value):
        if value is None:
            return ""
        number = float(value)
        if number.is_integer():
            return str(int(number))
        return f"{number:.4f}".rstrip("0").rstrip(".")
