from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
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
from src.ui.dialogs.finished_inventory_dialog import (
    FinishedInventoryDialog,
)


class FinishedInventoryPendingReceiptsDialog(QDialog):
    HEADERS = [
        "Work Order",
        "Product",
        "Final OP",
        "Final OP Qty",
        "Received",
        "Available",
    ]

    def __init__(
        self,
        parent=None,
        service=None,
    ):
        super().__init__(parent)
        self._owns_service = service is None
        self.service = (
            service or FinishedInventoryService()
        )
        self.rows = []

        self.setWindowTitle(
            "Finished Inventory Pending Receipts"
        )
        self.resize(920, 560)

        self.summary_label = QLabel()
        self.table = QTableWidget()
        self.refresh_button = QPushButton("Refresh")
        self.receive_button = QPushButton(
            "Receive Selected"
        )
        self.close_button = QPushButton("Close")

        self._build_ui()
        self._configure_table()
        self._connect_events()
        self.load_pending()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.addWidget(self.summary_label)
        root.addWidget(self.table, 1)

        buttons = QHBoxLayout()
        buttons.addWidget(self.refresh_button)
        buttons.addWidget(self.receive_button)
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
            0,
            QHeaderView.Stretch,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.Stretch,
        )

    def _connect_events(self):
        self.refresh_button.clicked.connect(
            self.load_pending
        )
        self.receive_button.clicked.connect(
            self.receive_selected
        )
        self.close_button.clicked.connect(
            self.accept
        )
        self.table.itemSelectionChanged.connect(
            self._update_receive_state
        )
        self.table.itemDoubleClicked.connect(
            lambda _item: self.receive_selected()
        )

    def load_pending(self):
        try:
            self.rows = list(
                self.service.get_pending_receipts()
                or []
            )
            self.table.setRowCount(len(self.rows))
            total_available = 0

            for row_index, row in enumerate(
                self.rows
            ):
                available = int(
                    row.get("available_qty", 0)
                    or 0
                )
                total_available += available
                values = [
                    row.get("work_order", ""),
                    row.get("product_code", ""),
                    row.get("final_operation", 0),
                    row.get("final_op_qty", 0),
                    row.get("received_qty", 0),
                    available,
                ]
                for column_index, value in enumerate(
                    values
                ):
                    item = QTableWidgetItem(
                        str(value)
                    )
                    if column_index >= 2:
                        item.setTextAlignment(
                            Qt.AlignCenter
                        )
                    self.table.setItem(
                        row_index,
                        column_index,
                        item,
                    )

            self.summary_label.setText(
                f"Pending Work Orders: {len(self.rows)}"
                f" | Available Qty: {total_available}"
            )
            if self.rows:
                self.table.selectRow(0)
            self._update_receive_state()
        except Exception as error:
            self.rows = []
            self.table.setRowCount(0)
            self.receive_button.setEnabled(False)
            QMessageBox.warning(
                self,
                "Pending Receipts",
                str(error),
            )

    def receive_selected(self):
        row_index = self.table.currentRow()
        if not 0 <= row_index < len(self.rows):
            return

        row = self.rows[row_index]
        dialog = FinishedInventoryDialog(
            parent=self,
            service=self.service,
        )
        dialog.work_order.setText(
            str(row.get("work_order", ""))
        )
        dialog.product_code.setText(
            str(row.get("product_code", ""))
        )
        available = int(
            row.get("available_qty", 0) or 0
        )
        dialog.qty.setMaximum(
            max(available, 0)
        )
        dialog.qty.setValue(
            max(available, 0)
        )
        dialog.refresh_capacity()

        if dialog.exec() != QDialog.Accepted:
            return
        try:
            self.service.create_inventory(
                dialog.get_data()
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Receipt Error",
                str(error),
            )
            return

        self.load_pending()

    def _update_receive_state(self):
        row_index = self.table.currentRow()
        enabled = (
            0 <= row_index < len(self.rows)
            and int(
                self.rows[row_index].get(
                    "available_qty",
                    0,
                )
                or 0
            )
            > 0
        )
        self.receive_button.setEnabled(enabled)

    def closeEvent(self, event):
        if self._owns_service:
            self.service.close()
        super().closeEvent(event)
