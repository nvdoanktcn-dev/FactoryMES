from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class StockInDialog(QDialog):
    """
    Dialog dùng cho Add/Edit phiếu Nhập kho.
    """

    def __init__(self, parent=None, stock_in=None):
        super().__init__(parent)

        self.stock_in = stock_in

        self.setWindowTitle(
            "Add Stock In" if stock_in is None else "Edit Stock In"
        )

        self.resize(420, 320)

        self.stock_in_date = QDateEdit()
        self.stock_in_date.setCalendarPopup(True)
        self.stock_in_date.setDisplayFormat("yyyy-MM-dd")
        self.stock_in_date.setDate(QDate.currentDate())

        self.item_code = QLineEdit()

        self.qty = QDoubleSpinBox()
        self.qty.setRange(0, 1_000_000)
        self.qty.setDecimals(2)

        self.supplier = QLineEdit()
        self.remark = QLineEdit()

        self.build_ui()

        if self.stock_in is not None:
            self.load_stock_in()

    def build_ui(self):
        root_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        form_layout.addRow("Date *", self.stock_in_date)
        form_layout.addRow("Item Code *", self.item_code)
        form_layout.addRow("Qty", self.qty)
        form_layout.addRow("Supplier", self.supplier)
        form_layout.addRow("Remark", self.remark)

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

    def load_stock_in(self):
        if self.stock_in.stock_in_date:
            self.stock_in_date.setDate(
                QDate(
                    self.stock_in.stock_in_date.year,
                    self.stock_in.stock_in_date.month,
                    self.stock_in.stock_in_date.day,
                )
            )

        self.item_code.setText(self.stock_in.item_code or "")
        self.qty.setValue(self.stock_in.qty or 0)
        self.supplier.setText(self.stock_in.supplier or "")
        self.remark.setText(self.stock_in.remark or "")

    def validate_and_accept(self):
        item_code = self.item_code.text().strip()

        if not item_code:
            QMessageBox.warning(
                self, "Validation", "Item Code is required."
            )
            self.item_code.setFocus()
            return

        self.accept()

    def get_data(self):
        qdate = self.stock_in_date.date()

        return {
            "stock_in_date": date(
                qdate.year(), qdate.month(), qdate.day()
            ),
            "item_code": self.item_code.text().strip().upper(),
            "qty": self.qty.value(),
            "supplier": self.supplier.text().strip(),
            "remark": self.remark.text().strip(),
        }
