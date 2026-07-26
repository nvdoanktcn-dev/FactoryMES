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


class CNCProductionLogDialog(QDialog):
    """
    Dialog dùng cho Add/Edit thủ công một dòng log sản xuất CNC.

    Phần lớn dữ liệu log đến từ import Excel (CNCImporter); dialog
    này phục vụ chỉnh sửa hoặc bổ sung log khi cần.
    """

    def __init__(self, parent=None, log=None):
        super().__init__(parent)

        self.log = log

        self.setWindowTitle(
            "Add CNC Production Log"
            if log is None
            else "Edit CNC Production Log"
        )

        self.resize(460, 480)

        self.log_date = QDateEdit()
        self.log_date.setCalendarPopup(True)
        self.log_date.setDisplayFormat("yyyy-MM-dd")
        self.log_date.setDate(QDate.currentDate())

        self.machine_name = QLineEdit()
        self.work_order_no = QLineEdit()
        self.product_name = QLineEdit()
        self.operator_name = QLineEdit()
        self.operation = QLineEdit()
        self.shift = QLineEdit()

        self.actual_pcs = self._build_spinbox()
        self.standard_pcs = self._build_spinbox()
        self.total_ng = self._build_spinbox()
        self.qty_ok = self._build_spinbox()

        self.build_ui()

        if self.log is not None:
            self.load_log()

    @staticmethod
    def _build_spinbox():
        spinbox = QDoubleSpinBox()
        spinbox.setRange(0, 1_000_000)
        spinbox.setDecimals(2)
        return spinbox

    def build_ui(self):
        root_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        form_layout.addRow("Log Date", self.log_date)
        form_layout.addRow("Machine Name *", self.machine_name)
        form_layout.addRow("Work Order No *", self.work_order_no)
        form_layout.addRow("Product Name", self.product_name)
        form_layout.addRow("Operator", self.operator_name)
        form_layout.addRow("Operation (OP)", self.operation)
        form_layout.addRow("Shift", self.shift)
        form_layout.addRow("Actual PCS", self.actual_pcs)
        form_layout.addRow("Standard PCS", self.standard_pcs)
        form_layout.addRow("Qty OK", self.qty_ok)
        form_layout.addRow("Total NG", self.total_ng)

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

    def load_log(self):
        if self.log.log_date:
            self.log_date.setDate(
                QDate(
                    self.log.log_date.year,
                    self.log.log_date.month,
                    self.log.log_date.day,
                )
            )

        self.machine_name.setText(self.log.machine_name or "")
        self.work_order_no.setText(self.log.work_order_no or "")
        self.product_name.setText(self.log.product_name or "")
        self.operator_name.setText(self.log.operator_name or "")
        self.operation.setText(self.log.operation or "")
        self.shift.setText(self.log.shift or "")
        self.actual_pcs.setValue(self.log.actual_pcs or 0)
        self.standard_pcs.setValue(self.log.standard_pcs or 0)
        self.qty_ok.setValue(self.log.qty_ok or 0)
        self.total_ng.setValue(self.log.total_ng or 0)

    def validate_and_accept(self):
        machine_name = self.machine_name.text().strip()
        work_order_no = self.work_order_no.text().strip()

        if not machine_name:
            QMessageBox.warning(
                self, "Validation", "Machine Name is required."
            )
            self.machine_name.setFocus()
            return

        if not work_order_no:
            QMessageBox.warning(
                self, "Validation", "Work Order No is required."
            )
            self.work_order_no.setFocus()
            return

        self.accept()

    def get_data(self):
        qdate = self.log_date.date()

        return {
            "log_date": date(
                qdate.year(), qdate.month(), qdate.day()
            ),
            "machine_name": self.machine_name.text().strip(),
            "work_order_no": self.work_order_no.text().strip(),
            "product_name": self.product_name.text().strip(),
            "operator_name": self.operator_name.text().strip(),
            "operation": self.operation.text().strip(),
            "shift": self.shift.text().strip(),
            "actual_pcs": self.actual_pcs.value(),
            "standard_pcs": self.standard_pcs.value(),
            "qty_ok": self.qty_ok.value(),
            "total_ng": self.total_ng.value(),
        }
