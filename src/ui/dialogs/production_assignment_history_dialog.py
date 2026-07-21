from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from src.services.production_assignment_history_service import (
    ProductionAssignmentHistoryService,
)


class ProductionAssignmentHistoryDialog(QDialog):
    """
    Hiển thị lịch sử thay đổi của một Production Assignment.
    """

    HEADERS = [
        "ID",
        "Changed At",
        "Action",
        "Old Status",
        "New Status",
        "Old Machine",
        "New Machine",
        "Old Employee",
        "New Employee",
        "Old Shift",
        "New Shift",
        "Changed By",
        "Remark",
    ]

    def __init__(
        self,
        parent=None,
        assignment=None,
        session=None,
    ):
        super().__init__(parent)

        self.assignment = assignment
        self.session = session

        if self.assignment is None:
            raise ValueError(
                "Production Assignment is required."
            )

        if self.session is None:
            raise ValueError(
                "SQLAlchemy session is required."
            )

        self.history_service = (
            ProductionAssignmentHistoryService(
                session=self.session
            )
        )

        self.setWindowTitle(
            (
                "Production Assignment History "
                f"#{self.assignment.id}"
            )
        )

        self.resize(
            1500,
            760,
        )

        self.setMinimumSize(
            1000,
            600,
        )

        self.assignment_label = QLabel(
            self
        )

        self.table = QTableWidget(
            self
        )

        self.detail_label = QLabel(
            "History Detail",
            self,
        )

        self.detail_text = QTextEdit(
            self
        )
        self.detail_text.setReadOnly(
            True
        )

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Close,
            parent=self,
        )

        self._row_histories = []

        self._build_ui()
        self._configure_table()
        self._connect_events()
        self._apply_style()
        self.load_history()

    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):
        self.assignment_label.setText(
            (
                f"Assignment #{self.assignment.id}"
                f"  |  Production Order ID: "
                f"{self.assignment.production_order_id}"
                f"  |  Current Status: "
                f"{self.assignment.status}"
                f"  |  Machine: "
                f"{self.assignment.machine_code or '-'}"
                f"  |  Employee: "
                f"{self.assignment.employee_code or '-'}"
                f"  |  Shift: "
                f"{self.assignment.shift or '-'}"
            )
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            14,
            14,
            14,
            14,
        )

        layout.setSpacing(
            10
        )

        layout.addWidget(
            self.assignment_label
        )

        layout.addWidget(
            self.table,
            1,
        )

        layout.addWidget(
            self.detail_label
        )

        layout.addWidget(
            self.detail_text
        )

        layout.addWidget(
            self.button_box
        )

    def _configure_table(self):
        self.table.setColumnCount(
            len(self.HEADERS)
        )

        self.table.setHorizontalHeaderLabels(
            self.HEADERS
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SingleSelection
        )

        self.table.setEditTriggers(
            QTableWidget.NoEditTriggers
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
        self.button_box.rejected.connect(
            self.reject
        )

        self.button_box.accepted.connect(
            self.accept
        )

        self.table.itemSelectionChanged.connect(
            self._show_selected_detail
        )

        self.table.cellDoubleClicked.connect(
            self._show_selected_detail
        )

    def _apply_style(self):
        self.assignment_label.setStyleSheet(
            (
                "font-size:14px;"
                "font-weight:bold;"
                "color:#263238;"
            )
        )

        self.detail_label.setStyleSheet(
            (
                "font-size:13px;"
                "font-weight:bold;"
                "color:#37474F;"
            )
        )

        self.detail_text.setMinimumHeight(
            170
        )

    # ==========================================================
    # Data
    # ==========================================================

    def load_history(self):
        try:
            histories = (
                self.history_service
                .get_by_assignment_id(
                    self.assignment.id
                )
            )

            self._row_histories = list(
                histories or []
            )

            self.table.setRowCount(
                len(self._row_histories)
            )

            for row_index, history in enumerate(
                self._row_histories
            ):
                values = [
                    history.id,
                    self._format_datetime(
                        history.changed_at
                    ),
                    history.action,
                    history.old_status,
                    history.new_status,
                    history.old_machine_code,
                    history.new_machine_code,
                    history.old_employee_code,
                    history.new_employee_code,
                    history.old_shift,
                    history.new_shift,
                    history.changed_by,
                    history.remark,
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
                        2,
                        3,
                        4,
                        9,
                        10,
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

            if self._row_histories:
                self.table.selectRow(
                    0
                )
                self._show_selected_detail()
            else:
                self.detail_text.setPlainText(
                    "No history records found."
                )

        except Exception as error:
            QMessageBox.warning(
                self,
                "Production Assignment History",
                str(error),
            )

    # ==========================================================
    # Detail
    # ==========================================================

    def _show_selected_detail(
        self,
        *_,
    ):
        selected_rows = (
            self.table
            .selectionModel()
            .selectedRows()
        )

        if not selected_rows:
            self.detail_text.clear()
            return

        row_index = selected_rows[0].row()

        if not (
            0
            <= row_index
            < len(self._row_histories)
        ):
            self.detail_text.clear()
            return

        history = self._row_histories[
            row_index
        ]

        old_data = self._parse_json(
            history.old_data_json
        )

        new_data = self._parse_json(
            history.new_data_json
        )

        lines = [
            f"History ID: {history.id}",
            f"Assignment ID: {history.assignment_id}",
            (
                "Production Order ID: "
                f"{history.production_order_id}"
            ),
            f"Action: {history.action}",
            (
                "Changed At: "
                f"{self._format_datetime(history.changed_at)}"
            ),
            f"Changed By: {history.changed_by or ''}",
            "",
            "OLD DATA",
            self._pretty_json(
                old_data
            ),
            "",
            "NEW DATA",
            self._pretty_json(
                new_data
            ),
        ]

        if history.remark:
            lines.extend(
                [
                    "",
                    f"Remark: {history.remark}",
                ]
            )

        self.detail_text.setPlainText(
            "\n".join(
                lines
            )
        )

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _parse_json(
        value,
    ):
        text = str(
            value or ""
        ).strip()

        if not text:
            return {}

        try:
            parsed = json.loads(
                text
            )

            if isinstance(
                parsed,
                dict,
            ):
                return parsed

            return {
                "value": parsed
            }

        except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            return {
                "raw": text
            }

    @staticmethod
    def _pretty_json(
        value,
    ):
        return json.dumps(
            value or {},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
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

        if callable(
            formatter
        ):
            return formatter(
                "%Y-%m-%d %H:%M:%S"
            )

        return str(
            value
        )
