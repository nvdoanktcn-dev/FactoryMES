from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.services.finished_inventory_import_history_service import (
    FinishedInventoryImportHistoryService,
)


class FinishedInventoryImportHistoryDialog(QDialog):
    HEADERS = [
        "ID",
        "Time",
        "File",
        "Rows",
        "Created",
        "Skipped",
        "Failed",
        "Duration",
        "Status",
        "Message",
    ]

    def __init__(
        self,
        parent=None,
        service=None,
    ):
        super().__init__(parent)
        self._owns_service = service is None
        self.service = (
            service
            or FinishedInventoryImportHistoryService()
        )
        self.records = []

        self.setWindowTitle(
            "Finished Inventory Import History"
        )
        self.resize(1250, 620)

        self.summary_label = QLabel()
        self.table = QTableWidget()
        self.refresh_button = QPushButton("Refresh")
        self.rollback_button = QPushButton(
            "Rollback Selected Import"
        )
        self.close_button = QPushButton("Close")

        self._build_ui()
        self._configure_table()
        self._connect_events()
        self.load_history()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.addWidget(self.summary_label)
        root.addWidget(self.table, 1)

        buttons = QHBoxLayout()
        buttons.addWidget(self.refresh_button)
        buttons.addWidget(self.rollback_button)
        buttons.addStretch()
        buttons.addWidget(self.close_button)
        root.addLayout(buttons)

    def _configure_table(self):
        self.table.setColumnCount(len(self.HEADERS))
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
            2,
            QHeaderView.Stretch,
        )
        header.setSectionResizeMode(
            9,
            QHeaderView.Stretch,
        )

    def _connect_events(self):
        self.refresh_button.clicked.connect(
            self.load_history
        )
        self.rollback_button.clicked.connect(
            self.rollback_selected
        )
        self.close_button.clicked.connect(self.accept)
        self.table.itemSelectionChanged.connect(
            self._update_rollback_state
        )

    def load_history(self):
        try:
            self.records = list(
                self.service.get_recent(100)
            )
            self.table.setRowCount(len(self.records))

            for row_index, record in enumerate(
                self.records
            ):
                values = [
                    record.id,
                    (
                        record.import_time.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if record.import_time
                        else ""
                    ),
                    record.file_name or "",
                    record.total_rows or 0,
                    record.inserted_rows or 0,
                    record.updated_rows or 0,
                    record.failed_rows or 0,
                    f"{float(record.duration or 0):.3f}s",
                    record.status or "",
                    record.message or "",
                ]

                for column_index, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    if column_index in {
                        0, 3, 4, 5, 6, 7, 8
                    }:
                        item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(
                        row_index,
                        column_index,
                        item,
                    )

            self.summary_label.setText(
                f"Recent imports: {len(self.records)}"
            )
            if self.records:
                self.table.selectRow(0)
            self._update_rollback_state()
        except Exception as error:
            QMessageBox.warning(
                self,
                "Import History",
                str(error),
            )

    def selected_record(self):
        rows = (
            self.table.selectionModel().selectedRows()
        )
        if not rows:
            return None
        index = rows[0].row()
        if 0 <= index < len(self.records):
            return self.records[index]
        return None

    def _update_rollback_state(self):
        record = self.selected_record()
        status = str(
            getattr(record, "status", "") or ""
        ).upper()
        self.rollback_button.setEnabled(
            status in {"SUCCESS", "PARTIAL"}
        )

    def rollback_selected(self):
        record = self.selected_record()
        if record is None:
            return

        answer = QMessageBox.question(
            self,
            "Confirm Import Rollback",
            (
                f"Delete all records created by import "
                f"#{record.id}?\n\n"
                "Rollback is allowed only when those "
                "records have not changed."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            result = self.service.rollback_import(
                record.id
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

    def closeEvent(self, event):
        if self._owns_service:
            self.service.close()
        super().closeEvent(event)
