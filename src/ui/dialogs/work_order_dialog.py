from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from src.services.product_service import ProductService


class WorkOrderDialog(QDialog):
    PRIORITIES = ["LOW", "NORMAL", "HIGH", "URGENT"]
    STATUSES = [
        "PLANNED",
        "RELEASED",
        "IN_PROGRESS",
        "ON_HOLD",
        "COMPLETED",
        "CANCELLED",
    ]

    def __init__(self, parent=None, work_order=None):
        super().__init__(parent)
        self.work_order = work_order
        self.product_service = ProductService()

        self.setWindowTitle("Edit Work Order" if work_order else "Add Work Order")
        self.setMinimumWidth(520)

        self.work_order_no_edit = QLineEdit(self)
        self.product_combo = QComboBox(self)
        self.product_combo.setEditable(True)

        self.plan_qty_spin = QSpinBox(self)
        self.plan_qty_spin.setRange(1, 2_000_000_000)

        self.start_date_edit = QDateEdit(self)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")

        self.due_date_edit = QDateEdit(self)
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDisplayFormat("yyyy-MM-dd")

        self.priority_combo = QComboBox(self)
        self.priority_combo.addItems(self.PRIORITIES)

        self.status_combo = QComboBox(self)
        self.status_combo.addItems(self.STATUSES)

        self.remark_edit = QTextEdit(self)
        self.remark_edit.setMaximumHeight(100)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel,
            parent=self,
        )

        form = QFormLayout()
        form.addRow("Work Order No *", self.work_order_no_edit)
        form.addRow("Product Code *", self.product_combo)
        form.addRow("Plan Qty *", self.plan_qty_spin)
        form.addRow("Start Date *", self.start_date_edit)
        form.addRow("Due Date *", self.due_date_edit)
        form.addRow("Priority", self.priority_combo)
        form.addRow("Status", self.status_combo)
        form.addRow("Remark", self.remark_edit)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self._accept_if_valid)
        self.button_box.rejected.connect(self.reject)
        self.start_date_edit.dateChanged.connect(self._sync_due_date)

        self._load_products()
        self._load_work_order()

    def _load_products(self):
        products = self.product_service.get_all_products()
        self.product_combo.clear()

        for product in products:
            code = str(product.product_code or "").strip().upper()
            if not code:
                continue

            name = str(
                getattr(product, "product_name_vi", "")
                or getattr(product, "product_name_cn", "")
                or ""
            ).strip()
            display = f"{code} - {name}" if name else code
            self.product_combo.addItem(display, code)

    def _load_work_order(self):
        today = QDate.currentDate()

        if self.work_order is None:
            self.start_date_edit.setDate(today)
            self.due_date_edit.setDate(today.addDays(7))
            self.plan_qty_spin.setValue(1)
            self.priority_combo.setCurrentText("NORMAL")
            self.status_combo.setCurrentText("PLANNED")
            return

        self.work_order_no_edit.setText(str(self.work_order.work_order_no or ""))
        self.work_order_no_edit.setReadOnly(True)

        product_code = str(self.work_order.product_code or "").strip().upper()
        index = self.product_combo.findData(product_code)
        if index >= 0:
            self.product_combo.setCurrentIndex(index)
        else:
            self.product_combo.setEditText(product_code)

        self.plan_qty_spin.setValue(int(self.work_order.plan_qty or 1))
        self.start_date_edit.setDate(self._to_qdate(self.work_order.start_date))
        self.due_date_edit.setDate(self._to_qdate(self.work_order.due_date))
        self.priority_combo.setCurrentText(str(self.work_order.priority or "NORMAL").upper())
        self.status_combo.setCurrentText(str(self.work_order.status or "PLANNED").upper())
        self.remark_edit.setPlainText(str(self.work_order.remark or ""))

    def _sync_due_date(self, start_date):
        if self.due_date_edit.date() < start_date:
            self.due_date_edit.setDate(start_date)

    def _accept_if_valid(self):
        if not self.work_order_no_edit.text().strip():
            QMessageBox.warning(self, "Work Order", "Work Order No is required.")
            return
        if not self._selected_product_code():
            QMessageBox.warning(self, "Work Order", "Product Code is required.")
            return
        if self.due_date_edit.date() < self.start_date_edit.date():
            QMessageBox.warning(
                self,
                "Work Order",
                "Due Date cannot be before Start Date.",
            )
            return
        self.accept()

    def get_data(self):
        return {
            "work_order_no": self.work_order_no_edit.text().strip().upper(),
            "product_code": self._selected_product_code(),
            "plan_qty": self.plan_qty_spin.value(),
            "start_date": self.start_date_edit.date().toString("yyyy-MM-dd"),
            "due_date": self.due_date_edit.date().toString("yyyy-MM-dd"),
            "priority": self.priority_combo.currentText().strip().upper(),
            "status": self.status_combo.currentText().strip().upper(),
            "remark": self.remark_edit.toPlainText().strip() or None,
        }

    def _selected_product_code(self):
        current_data = self.product_combo.currentData()
        if current_data:
            return str(current_data).strip().upper()

        text = self.product_combo.currentText().strip()
        if " - " in text:
            text = text.split(" - ", 1)[0]
        return text.upper()

    @staticmethod
    def _to_qdate(value):
        if value is None:
            return QDate.currentDate()

        year = getattr(value, "year", None)
        month = getattr(value, "month", None)
        day = getattr(value, "day", None)
        if all(part is not None for part in (year, month, day)):
            return QDate(int(year), int(month), int(day))

        parsed = QDate.fromString(str(value), "yyyy-MM-dd")
        return parsed if parsed.isValid() else QDate.currentDate()

    def closeEvent(self, event):
        close_method = getattr(self.product_service, "close", None)
        if callable(close_method):
            close_method()
        super().closeEvent(event)
