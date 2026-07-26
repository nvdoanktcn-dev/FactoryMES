from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class CNCMachineDialog(QDialog):
    """
    Dialog dùng chung cho Add và Edit CNC Machine.
    """

    STATUSES = ["ACTIVE", "INACTIVE"]

    def __init__(self, parent=None, machine=None):
        super().__init__(parent)

        self.machine = machine

        self.setWindowTitle(
            "Add CNC Machine"
            if machine is None
            else "Edit CNC Machine"
        )

        self.resize(440, 400)

        self.machine_code = QLineEdit()
        self.machine_name = QLineEdit()
        self.machine_type = QLineEdit()
        self.controller = QLineEdit()

        self.axis_count = QSpinBox()
        self.axis_count.setRange(0, 20)

        self.location = QLineEdit()
        self.remark = QLineEdit()

        self.status = QComboBox()
        self.status.addItems(self.STATUSES)

        self.build_ui()

        if self.machine is not None:
            self.load_machine()

    def build_ui(self):
        root_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        form_layout.addRow("Machine Code *", self.machine_code)
        form_layout.addRow("Machine Name *", self.machine_name)
        form_layout.addRow("Machine Type", self.machine_type)
        form_layout.addRow("Controller", self.controller)
        form_layout.addRow("Axis Count", self.axis_count)
        form_layout.addRow("Location", self.location)
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

    def load_machine(self):
        self.machine_code.setText(self.machine.machine_code or "")
        self.machine_code.setReadOnly(True)

        self.machine_name.setText(self.machine.machine_name or "")
        self.machine_type.setText(self.machine.machine_type or "")
        self.controller.setText(self.machine.controller or "")
        self.axis_count.setValue(self.machine.axis_count or 0)
        self.location.setText(self.machine.location or "")
        self.remark.setText(self.machine.remark or "")

        self.set_combo_value(
            self.status, self.machine.status or "ACTIVE"
        )

    def validate_and_accept(self):
        machine_code = self.machine_code.text().strip().upper()
        machine_name = self.machine_name.text().strip()

        if not machine_code:
            QMessageBox.warning(
                self, "Validation", "Machine Code is required."
            )
            self.machine_code.setFocus()
            return

        if not machine_name:
            QMessageBox.warning(
                self, "Validation", "Machine Name is required."
            )
            self.machine_name.setFocus()
            return

        self.accept()

    def get_data(self):
        return {
            "machine_code": self.machine_code.text().strip().upper(),
            "machine_name": self.machine_name.text().strip(),
            "machine_type": self.machine_type.text().strip(),
            "controller": self.controller.text().strip(),
            "axis_count": self.axis_count.value(),
            "location": self.location.text().strip(),
            "status": self.status.currentText().strip().upper(),
            "remark": self.remark.text().strip(),
        }

    @staticmethod
    def set_combo_value(combo, value):
        normalized = str(value or "").strip().upper()
        index = combo.findText(normalized)

        if index >= 0:
            combo.setCurrentIndex(index)
