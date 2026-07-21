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

from src.ui.controllers.production_assignment_controller import (
    ProductionAssignmentController,
)


class ProductionAssignmentPage(QWidget):
    HEADERS = [
        "ID",
        "Work Order",
        "Product",
        "OP",
        "Operation",
        "Machine",
        "Employee",
        "Shift",
        "Planned Start",
        "Planned Finish",
        "Status",
        "Remark",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._row_objects = []

        self.title_label = QLabel("Production Assignment", self)
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText(
            "Search Assignment, Work Order, Machine, Employee or Shift..."
        )

        self.status_filter = QComboBox(self)
        self.status_filter.addItems(
            [
                "ALL",
                "DRAFT",
                "RELEASED",
                "IN_PROGRESS",
                "ON_HOLD",
                "COMPLETED",
                "CANCELLED",
            ]
        )

        self.btn_add = QPushButton("Add", self)
        self.btn_edit = QPushButton("Edit", self)
        self.btn_history = QPushButton(
            "History",
            self,
        )
        self.btn_release = QPushButton("Release", self)
        self.btn_start = QPushButton("Start", self)
        self.btn_hold = QPushButton("Hold", self)
        self.btn_complete = QPushButton("Complete", self)
        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_refresh = QPushButton("Refresh", self)

        self.table = QTableWidget(self)
        self.status_label = QLabel("", self)

        self.controller = ProductionAssignmentController(page=self)

        self._build_ui()
        self._configure_table()
        self._connect_events()
        self._apply_style()
        self.controller.load_assignments()
        

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Search", self))
        filters.addWidget(self.search_box, 1)
        filters.addWidget(QLabel("Status", self))
        filters.addWidget(self.status_filter)

        buttons = QHBoxLayout()
        for button in (
            self.btn_add,
            self.btn_edit,
            self.btn_history,
            self.btn_release,
            self.btn_start,
            self.btn_hold,
            self.btn_complete,
            self.btn_cancel,
            self.btn_refresh,
        ):
            buttons.addWidget(button)
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
        self.search_box.textChanged.connect(
            self.controller.load_assignments
        )
        self.status_filter.currentTextChanged.connect(
            self.controller.load_assignments
        )
        self.btn_add.clicked.connect(self.controller.add_assignment)
        self.btn_edit.clicked.connect(self.controller.edit_selected)
        self.btn_release.clicked.connect(self.controller.release_selected)
        self.btn_start.clicked.connect(self.controller.start_selected)
        self.btn_hold.clicked.connect(self.controller.hold_selected)
        self.btn_complete.clicked.connect(self.controller.complete_selected)
        self.btn_cancel.clicked.connect(self.controller.cancel_selected)
        self.btn_refresh.clicked.connect(self.controller.load_assignments)
        self.table.doubleClicked.connect(self.controller.edit_selected)
        self.btn_history.clicked.connect(
            self.controller.show_selected_history
        )

    def _apply_style(self):
        self.title_label.setStyleSheet(
            "font-size:24px;font-weight:bold;color:#263238;"
        )
        self.status_label.setStyleSheet("color:#546E7A;")

        for button in (
            self.btn_add,
            self.btn_edit,
            self.btn_history,
            self.btn_release,
            self.btn_start,
            self.btn_hold,
            self.btn_complete,
            self.btn_cancel,
            self.btn_refresh,
        ):
            button.setMinimumHeight(32)

    def set_assignments(self, rows):
        self._row_objects = [assignment for assignment, _ in rows]
        self.table.setRowCount(len(rows))

        for row_index, (assignment, production_order) in enumerate(rows):
            values = [
                assignment.id,
                production_order.work_order_no if production_order else "",
                production_order.product_code if production_order else "",
                (
                    f"OP{production_order.operation_no}"
                    if production_order
                    else ""
                ),
                production_order.operation_name if production_order else "",
                assignment.machine_code,
                assignment.employee_code,
                assignment.shift,
                self._format_datetime(assignment.planned_start),
                self._format_datetime(assignment.planned_finish),
                assignment.status,
                assignment.remark,
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(
                    "" if value is None else str(value)
                )
                if column_index in {0, 3, 7, 10}:
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_index, column_index, item)

        self.table.resizeRowsToContents()

    def selected_assignment(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None

        row_index = selected_rows[0].row()
        if not 0 <= row_index < len(self._row_objects):
            return None

        return self._row_objects[row_index]

    def set_status_message(self, message):
        self.status_label.setText(str(message or ""))

    def show_error(self, error):
        message = str(error)
        self.set_status_message(message)
        QMessageBox.warning(
            self,
            "Production Assignment Error",
            message,
        )

    def on_page_activated(self):
        self.controller.load_assignments()

    def closeEvent(self, event):
        self.controller.close()
        super().closeEvent(event)

    @staticmethod
    def _format_datetime(value):
        if value is None:
            return ""

        formatter = getattr(value, "strftime", None)
        if callable(formatter):
            return formatter("%Y-%m-%d %H:%M")

        return str(value)
