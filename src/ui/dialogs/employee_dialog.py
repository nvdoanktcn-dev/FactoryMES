from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class EmployeeDialog(QDialog):
    """
    Dialog dùng chung cho Add và Edit Employee.
    """

    STATUSES = [
        "ACTIVE",
        "INACTIVE",
    ]

    def __init__(
        self,
        parent=None,
        employee=None,
    ):
        super().__init__(parent)

        self.employee = employee

        self.setWindowTitle(
            "Add Employee"
            if employee is None
            else "Edit Employee"
        )

        self.resize(440, 340)

        self.employee_code = QLineEdit()
        self.employee_name = QLineEdit()
        self.department = QLineEdit()
        self.position = QLineEdit()

        self.status = QComboBox()
        self.status.addItems(self.STATUSES)

        self.build_ui()

        if self.employee is not None:
            self.load_employee()

    def build_ui(self):
        root_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        form_layout.addRow(
            "Employee Code *",
            self.employee_code,
        )

        form_layout.addRow(
            "Employee Name *",
            self.employee_name,
        )

        form_layout.addRow(
            "Department",
            self.department,
        )

        form_layout.addRow(
            "Position",
            self.position,
        )

        form_layout.addRow(
            "Status",
            self.status,
        )

        button_layout = QHBoxLayout()

        self.btn_save = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")

        self.btn_save.clicked.connect(
            self.validate_and_accept
        )

        self.btn_cancel.clicked.connect(
            self.reject
        )

        button_layout.addStretch()
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_cancel)

        root_layout.addLayout(form_layout)
        root_layout.addStretch()
        root_layout.addLayout(button_layout)

    def load_employee(self):
        self.employee_code.setText(
            self.employee.employee_code or ""
        )

        self.employee_code.setReadOnly(True)

        self.employee_name.setText(
            self.employee.employee_name or ""
        )

        self.department.setText(
            self.employee.department or ""
        )

        self.position.setText(
            getattr(
                self.employee,
                "position",
                "",
            )
            or ""
        )

        self.set_combo_value(
            self.status,
            self.employee.status or "ACTIVE",
        )

    def validate_and_accept(self):
        employee_code = (
            self.employee_code
            .text()
            .strip()
            .upper()
        )

        employee_name = (
            self.employee_name
            .text()
            .strip()
        )

        if not employee_code:
            QMessageBox.warning(
                self,
                "Validation",
                "Employee Code is required.",
            )

            self.employee_code.setFocus()
            return

        if not employee_name:
            QMessageBox.warning(
                self,
                "Validation",
                "Employee Name is required.",
            )

            self.employee_name.setFocus()
            return

        self.accept()

    def get_data(self):
        return {
            "employee_code": (
                self.employee_code
                .text()
                .strip()
                .upper()
            ),

            "employee_name": (
                self.employee_name
                .text()
                .strip()
            ),

            "department": (
                self.department
                .text()
                .strip()
            ),

            "position": (
                self.position
                .text()
                .strip()
            ),

            "status": (
                self.status
                .currentText()
                .strip()
                .upper()
            ),
        }

    @staticmethod
    def set_combo_value(
        combo,
        value,
    ):
        normalized = str(
            value or ""
        ).strip().upper()

        index = combo.findText(normalized)

        if index >= 0:
            combo.setCurrentIndex(index)