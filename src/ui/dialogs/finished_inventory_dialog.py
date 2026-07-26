from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class FinishedInventoryDialog(QDialog):
    """
    Dialog dùng cho Add/Edit Tồn kho thành phẩm.
    """

    def __init__(self, parent=None, inventory=None):
        super().__init__(parent)

        self.inventory = inventory

        self.setWindowTitle(
            "Add Finished Inventory"
            if inventory is None
            else "Edit Finished Inventory"
        )

        self.resize(420, 300)

        self.inventory_date = QDateEdit()
        self.inventory_date.setCalendarPopup(True)
        self.inventory_date.setDisplayFormat("yyyy-MM-dd")
        self.inventory_date.setDate(QDate.currentDate())

        self.work_order = QLineEdit()
        self.product_code = QLineEdit()

        self.qty = QSpinBox()
        self.qty.setRange(0, 10_000_000)

        self.build_ui()

        if self.inventory is not None:
            self.load_inventory()

    def build_ui(self):
        root_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        form_layout.addRow("Date *", self.inventory_date)
        form_layout.addRow("Work Order *", self.work_order)
        form_layout.addRow("Product Code *", self.product_code)
        form_layout.addRow("Qty", self.qty)

        button_layout = QHBoxLayout()

        self.btn_save = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")

        self.btn_save.clicked.connect(self.validate_and_accept)
        self.btn_cancel.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_cancel)

        root_layout.addLayout(form_layout)
        root_layout.addStretch()
        root_layout.addLayout(button_layout)

    def load_inventory(self):
        if self.inventory.inventory_date:
            self.inventory_date.setDate(
                QDate(
                    self.inventory.inventory_date.year,
                    self.inventory.inventory_date.month,
                    self.inventory.inventory_date.day,
                )
            )

        self.work_order.setText(self.inventory.work_order or "")
        self.product_code.setText(self.inventory.product_code or "")
        self.qty.setValue(self.inventory.qty or 0)

    def validate_and_accept(self):
        work_order = self.work_order.text().strip()
        product_code = self.product_code.text().strip()

        if not work_order:
            QMessageBox.warning(
                self, "Validation", "Work Order is required."
            )
            self.work_order.setFocus()
            return

        if not product_code:
            QMessageBox.warning(
                self, "Validation", "Product Code is required."
            )
            self.product_code.setFocus()
            return

        self.accept()

    def get_data(self):
        qdate = self.inventory_date.date()

        return {
            "inventory_date": date(
                qdate.year(), qdate.month(), qdate.day()
            ),
            "work_order": self.work_order.text().strip().upper(),
            "product_code": self.product_code.text().strip().upper(),
            "qty": self.qty.value(),
        }
