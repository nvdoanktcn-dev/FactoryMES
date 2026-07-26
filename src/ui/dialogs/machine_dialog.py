import re

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


class MachineDialog(QDialog):
    """
    Dialog dùng chung cho Add/Edit Machine.
    """

    MACHINE_TYPES = [
        "CNC",
        "ROBOT",
        "MANUAL",
        "INSPECTION",
        "OTHER",
    ]

    STATUSES = [
        "RUNNING",
        "MAINTENANCE",
        "STOPPED",
        "INACTIVE",
    ]

    def __init__(
        self,
        parent=None,
        machine=None,
    ):
        super().__init__(parent)

        self.machine = machine

        self.setWindowTitle(
            "Add Machine"
            if machine is None
            else "Edit Machine"
        )

        self.resize(480, 480)

        self.machine_code = QLineEdit()
        self.machine_name = QLineEdit()

        self.machine_type = QComboBox()
        self.machine_type.addItems(
            self.MACHINE_TYPES
        )

        self.line = QLineEdit()
        self.location = QLineEdit()
        self.brand = QLineEdit()
        self.model = QLineEdit()
        self.serial_number = QLineEdit()

        self.status = QComboBox()
        self.status.addItems(
            self.STATUSES
        )

        self.build_ui()
        self.machine_code.textChanged.connect(
            self.sync_machine_type_from_code
        )

        if self.machine is not None:
            self.load_machine()

    def build_ui(self):
        root_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        form_layout.addRow(
            "Machine Code *",
            self.machine_code,
        )
        form_layout.addRow(
            "Machine Name *",
            self.machine_name,
        )
        form_layout.addRow(
            "Machine Type",
            self.machine_type,
        )
        form_layout.addRow(
            "Line",
            self.line,
        )
        form_layout.addRow(
            "Location",
            self.location,
        )
        form_layout.addRow(
            "Brand",
            self.brand,
        )
        form_layout.addRow(
            "Model",
            self.model,
        )
        form_layout.addRow(
            "Serial Number",
            self.serial_number,
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
        button_layout.addWidget(
            self.btn_save
        )
        button_layout.addWidget(
            self.btn_cancel
        )

        root_layout.addLayout(form_layout)
        root_layout.addStretch()
        root_layout.addLayout(button_layout)

    def load_machine(self):
        self.machine_code.setText(
            self.machine.machine_code or ""
        )
        self.machine_code.setReadOnly(True)

        self.machine_name.setText(
            self.machine.machine_name or ""
        )

        self.set_combo_value(
            self.machine_type,
            self.machine.machine_type or "OTHER",
        )

        self.line.setText(
            self.machine.line or ""
        )
        self.location.setText(
            self.machine.location or ""
        )
        self.brand.setText(
            self.machine.brand or ""
        )
        self.model.setText(
            self.machine.model or ""
        )
        self.serial_number.setText(
            self.machine.serial_number or ""
        )

        self.set_combo_value(
            self.status,
            self.machine.status or "RUNNING",
        )

    def validate_and_accept(self):
        machine_code = (
            self.machine_code
            .text()
            .strip()
            .upper()
        )

        machine_name = (
            self.machine_name
            .text()
            .strip()
        )

        if not machine_code:
            QMessageBox.warning(
                self,
                "Validation",
                "Machine Code is required.",
            )
            self.machine_code.setFocus()
            return

        if not machine_name:
            QMessageBox.warning(
                self,
                "Validation",
                "Machine Name is required.",
            )
            self.machine_name.setFocus()
            return

        machine_type = (
            self.machine_type
            .currentText()
            .strip()
            .upper()
        )

        validation_error = (
            self.validate_code_and_type(
                machine_code,
                machine_type,
            )
        )

        if validation_error:
            QMessageBox.warning(
                self,
                "Validation",
                validation_error,
            )
            self.machine_code.setFocus()
            return

        self.accept()

    def sync_machine_type_from_code(
        self,
        value,
    ):
        if self.machine is not None:
            return

        code = str(value or "").strip().upper()

        if code.startswith("BL"):
            self.set_combo_value(
                self.machine_type,
                "CNC",
            )
        elif (
            code.startswith("BR")
            or code.startswith("ASK")
        ):
            self.set_combo_value(
                self.machine_type,
                "ROBOT",
            )

    @staticmethod
    def validate_code_and_type(
        machine_code,
        machine_type,
    ):
        code = str(
            machine_code or ""
        ).strip().upper()
        normalized_type = str(
            machine_type or ""
        ).strip().upper()

        br_match = re.fullmatch(
            r"BR(\d{2})",
            code,
        )
        is_valid_br = (
            br_match is not None
            and 1 <= int(br_match.group(1)) <= 11
        )
        is_valid_ask = (
            re.fullmatch(r"ASK\d+", code)
            is not None
        )
        is_valid_brask = (
            re.fullmatch(
                r"BRASK[A-Z0-9-]+",
                code,
            )
            is not None
        )

        if normalized_type == "CNC":
            if not code.startswith("BL"):
                return (
                    "CNC Machine Code must start with BL."
                )

        if normalized_type == "ROBOT":
            if not (
                is_valid_br
                or is_valid_ask
                or is_valid_brask
            ):
                return (
                    "ROBOT Machine Code must be "
                    "BR01-BR11, ASK followed by digits, "
                    "or start with BRASK."
                )

        if code.startswith("BL") and normalized_type != "CNC":
            return (
                "BL Machine Code requires Machine Type CNC."
            )

        if (
            code.startswith("BR")
            or code.startswith("ASK")
        ):
            if normalized_type != "ROBOT":
                return (
                    "BR/ASK/BRASK Machine Code requires "
                    "Machine Type ROBOT."
                )

            if not (
                is_valid_br
                or is_valid_ask
                or is_valid_brask
            ):
                return (
                    "Robot code must be BR01-BR11 "
                    "ASK followed by digits, "
                    "or start with BRASK."
                )

        return None

    def get_data(self):
        return {
            "machine_code": (
                self.machine_code
                .text()
                .strip()
                .upper()
            ),
            "machine_name": (
                self.machine_name
                .text()
                .strip()
            ),
            "machine_type": (
                self.machine_type
                .currentText()
                .strip()
                .upper()
            ),
            "line": self.line.text().strip(),
            "location": (
                self.location
                .text()
                .strip()
            ),
            "brand": (
                self.brand
                .text()
                .strip()
            ),
            "model": (
                self.model
                .text()
                .strip()
            ),
            "serial_number": (
                self.serial_number
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
        value = str(
            value or ""
        ).strip().upper()

        index = combo.findText(value)

        if index >= 0:
            combo.setCurrentIndex(index)
