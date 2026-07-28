from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.services.finished_inventory_service import (
    FinishedInventoryService,
)


class FinishedInventoryReceiptAuditDialog(QDialog):
    HEADERS = [
        "ID",
        "Time",
        "Record",
        "Action",
        "Source",
        "User",
        "Before",
        "After",
    ]

    def __init__(
        self,
        parent=None,
        service=None,
        username="System",
    ):
        super().__init__(parent)
        self.audit_username = str(username or "System")
        self._owns_service = service is None
        self.service = (
            service or FinishedInventoryService()
        )
        self.records = []
        self.filtered_records = []

        self.setWindowTitle(
            "Finished Inventory Receipt Audit History"
        )
        self.resize(1380, 650)

        self.action_filter = QComboBox()
        self.action_filter.addItems([
            "ALL",
            "CREATE",
            "UPDATE",
            "DELETE",
            "ROLLBACK",
        ])
        self.source_filter = QComboBox()
        self.source_filter.addItems([
            "ALL",
            "MANUAL",
            "EXCEL_IMPORT",
            "PENDING_RECEIPT",
            "ROLLBACK",
        ])
        self.summary_label = QLabel()
        self.table = QTableWidget()
        self.refresh_button = QPushButton("Refresh")
        self.rollback_button = QPushButton(
            "Rollback Selected"
        )
        self.close_button = QPushButton("Close")

        self._build_ui()
        self._configure_table()
        self._connect_events()
        self.load_history()

    def _build_ui(self):
        root = QVBoxLayout(self)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Action"))
        filters.addWidget(self.action_filter)
        filters.addWidget(QLabel("Source"))
        filters.addWidget(self.source_filter)
        filters.addStretch()
        filters.addWidget(self.summary_label)
        root.addLayout(filters)

        root.addWidget(self.table, 1)

        buttons = QHBoxLayout()
        buttons.addWidget(self.refresh_button)
        buttons.addWidget(self.rollback_button)
        buttons.addStretch()
        buttons.addWidget(self.close_button)
        root.addLayout(buttons)

    def _configure_table(self):
        self.table.setColumnCount(
            len(self.HEADERS)
        )
        self.table.setHorizontalHeaderLabels(
            self.HEADERS
        )
        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        header.setSectionResizeMode(
            6,
            QHeaderView.Stretch,
        )
        header.setSectionResizeMode(
            7,
            QHeaderView.Stretch,
        )

    def _connect_events(self):
        self.refresh_button.clicked.connect(
            self.load_history
        )
        self.rollback_button.clicked.connect(
            self.rollback_selected
        )
        self.close_button.clicked.connect(
            self.accept
        )
        self.action_filter.currentTextChanged.connect(
            self.apply_filters
        )
        self.source_filter.currentTextChanged.connect(
            self.apply_filters
        )
        self.table.itemSelectionChanged.connect(
            self._update_rollback_state
        )

    def load_history(self):
        try:
            self.records = list(
                self.service
                .get_receipt_audit_history(500)
                or []
            )
            self.apply_filters()
        except Exception as error:
            self.records = []
            self.filtered_records = []
            self.table.setRowCount(0)
            self.rollback_button.setEnabled(False)
            QMessageBox.warning(
                self,
                "Receipt Audit History",
                str(error),
            )

    def apply_filters(self):
        action_filter = (
            self.action_filter.currentText()
        )
        source_filter = (
            self.source_filter.currentText()
        )
        self.filtered_records = [
            record
            for record in self.records
            if (
                action_filter == "ALL"
                or self._action(record)
                == action_filter
            )
            and (
                source_filter == "ALL"
                or self._source(record)
                == source_filter
            )
        ]
        self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(
            len(self.filtered_records)
        )
        for row_index, record in enumerate(
            self.filtered_records
        ):
            values = [
                record.id,
                (
                    record.created_at.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if record.created_at
                    else ""
                ),
                record.record_id,
                self._action(record),
                self._source(record),
                record.username or "System",
                self._display_data(
                    record.old_value
                ),
                self._display_data(
                    record.new_value
                ),
            ]
            for column_index, value in enumerate(
                values
            ):
                item = QTableWidgetItem(str(value))
                if column_index <= 5:
                    item.setTextAlignment(
                        Qt.AlignCenter
                    )
                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.summary_label.setText(
            f"Showing {len(self.filtered_records)}"
            f" of {len(self.records)} audit record(s)"
        )
        if self.filtered_records:
            self.table.selectRow(0)
        self._update_rollback_state()

    def selected_record(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.filtered_records):
            return self.filtered_records[row]
        return None

    def _update_rollback_state(self):
        record = self.selected_record()
        self.rollback_button.setEnabled(
            record is not None
            and self._action(record)
            in {"CREATE", "UPDATE", "DELETE"}
        )

    def rollback_selected(self):
        record = self.selected_record()
        if record is None:
            return

        answer = QMessageBox.question(
            self,
            "Confirm Receipt Rollback",
            (
                f"Rollback {self._action(record)} "
                f"audit #{record.id}?\n\n"
                "Rollback will be blocked if the inventory "
                "record changed or violates Final OP limits."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            result = (
                self.service.rollback_receipt_audit(
                    record.id,
                    username=self.audit_username,
                )
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                "Rollback Blocked",
                str(error),
            )
            return

        QMessageBox.information(
            self,
            "Rollback Complete",
            result["message"],
        )
        self.load_history()

    @classmethod
    def _source(cls, record):
        for raw_value in (
            record.new_value,
            record.old_value,
        ):
            source = cls._json(raw_value).get(
                "source"
            )
            if source:
                return str(source).upper()
        return ""

    @staticmethod
    def _action(record):
        return str(
            record.action or ""
        ).strip().upper()

    @classmethod
    def _display_data(cls, raw_value):
        data = cls._json(raw_value).get("data")
        if not data:
            return ""
        fields = [
            ("work_order", "WO"),
            ("product_code", "Product"),
            ("inventory_date", "Date"),
            ("qty", "Qty"),
        ]
        return " | ".join(
            f"{label}: {data.get(key, '')}"
            for key, label in fields
            if key in data
        )

    @staticmethod
    def _json(value):
        if isinstance(value, dict):
            return value
        try:
            return dict(json.loads(value or "{}") or {})
        except (TypeError, ValueError):
            return {}

    def closeEvent(self, event):
        if self._owns_service:
            self.service.close()
        super().closeEvent(event)
