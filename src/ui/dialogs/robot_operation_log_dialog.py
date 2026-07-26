from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
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


class RobotOperationLogDialog(QDialog):
    """
    Dialog dùng cho Add/Edit log vận hành Robot.
    """

    STATUSES = ["COMPLETED", "RUNNING", "ERROR", "STOPPED"]

    def __init__(self, parent=None, log=None, robot_codes=None):
        super().__init__(parent)

        self.log = log

        self.setWindowTitle(
            "Add Robot Operation Log"
            if log is None
            else "Edit Robot Operation Log"
        )

        self.resize(460, 460)

        self.robot_code = QComboBox()
        self.robot_code.setEditable(True)
        self.robot_code.addItems(list(robot_codes or []))

        self.log_date = QDateEdit()
        self.log_date.setCalendarPopup(True)
        self.log_date.setDisplayFormat("yyyy-MM-dd")
        self.log_date.setDate(QDate.currentDate())

        self.shift = QLineEdit()

        self.output_qty = self._build_spinbox()
        self.ng_qty = self._build_spinbox()

        self.error_code = QLineEdit()
        self.error_message = QLineEdit()
        self.remark = QLineEdit()

        self.status = QComboBox()
        self.status.addItems(self.STATUSES)

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

        form_layout.addRow("Robot Code *", self.robot_code)
        form_layout.addRow("Log Date", self.log_date)
        form_layout.addRow("Shift", self.shift)
        form_layout.addRow("Output Qty", self.output_qty)
        form_layout.addRow("NG Qty", self.ng_qty)
        form_layout.addRow("Error Code", self.error_code)
        form_layout.addRow("Error Message", self.error_message)
        form_layout.addRow("Status", self.status)
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

    def load_log(self):
        self.robot_code.setCurrentText(self.log.robot_code or "")

        if self.log.log_date:
            self.log_date.setDate(
                QDate(
                    self.log.log_date.year,
                    self.log.log_date.month,
                    self.log.log_date.day,
                )
            )

        self.shift.setText(self.log.shift or "")
        self.output_qty.setValue(self.log.output_qty or 0)
        self.ng_qty.setValue(self.log.ng_qty or 0)
        self.error_code.setText(self.log.error_code or "")
        self.error_message.setText(self.log.error_message or "")
        self.remark.setText(self.log.remark or "")

        self.set_combo_value(
            self.status, self.log.status or "COMPLETED"
        )

    def validate_and_accept(self):
        robot_code = self.robot_code.currentText().strip()

        if not robot_code:
            QMessageBox.warning(
                self, "Validation", "Robot Code is required."
            )
            self.robot_code.setFocus()
            return

        self.accept()

    def get_data(self):
        qdate = self.log_date.date()

        return {
            "robot_code": (
                self.robot_code.currentText().strip().upper()
            ),
            "log_date": date(
                qdate.year(), qdate.month(), qdate.day()
            ),
            "shift": self.shift.text().strip(),
            "output_qty": self.output_qty.value(),
            "ng_qty": self.ng_qty.value(),
            "error_code": self.error_code.text().strip(),
            "error_message": self.error_message.text().strip(),
            "status": self.status.currentText().strip().upper(),
            "remark": self.remark.text().strip(),
        }

    @staticmethod
    def set_combo_value(combo, value):
        normalized = str(value or "").strip().upper()
        index = combo.findText(normalized)

        if index >= 0:
            combo.setCurrentIndex(index)
