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


class RobotDialog(QDialog):
    """
    Dialog dùng chung cho Add và Edit Robot.
    """

    STATUSES = ["ACTIVE", "MAINTENANCE", "STOPPED"]

    def __init__(self, parent=None, robot=None):
        super().__init__(parent)

        self.robot = robot

        self.setWindowTitle(
            "Add Robot" if robot is None else "Edit Robot"
        )

        self.resize(440, 380)

        self.robot_code = QLineEdit()
        self.robot_name = QLineEdit()
        self.robot_type = QLineEdit()
        self.area = QLineEdit()
        self.station = QLineEdit()
        self.remark = QLineEdit()

        self.status = QComboBox()
        self.status.addItems(self.STATUSES)

        self.build_ui()

        if self.robot is not None:
            self.load_robot()

    def build_ui(self):
        root_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        form_layout.addRow("Robot Code *", self.robot_code)
        form_layout.addRow("Robot Name *", self.robot_name)
        form_layout.addRow("Robot Type", self.robot_type)
        form_layout.addRow("Area", self.area)
        form_layout.addRow("Station", self.station)
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

    def load_robot(self):
        self.robot_code.setText(self.robot.robot_code or "")
        self.robot_code.setReadOnly(True)

        self.robot_name.setText(self.robot.robot_name or "")
        self.robot_type.setText(self.robot.robot_type or "")
        self.area.setText(self.robot.area or "")
        self.station.setText(self.robot.station or "")
        self.remark.setText(self.robot.remark or "")

        self.set_combo_value(
            self.status, self.robot.status or "ACTIVE"
        )

    def validate_and_accept(self):
        robot_code = self.robot_code.text().strip().upper()
        robot_name = self.robot_name.text().strip()

        if not robot_code:
            QMessageBox.warning(
                self, "Validation", "Robot Code is required."
            )
            self.robot_code.setFocus()
            return

        if not robot_name:
            QMessageBox.warning(
                self, "Validation", "Robot Name is required."
            )
            self.robot_name.setFocus()
            return

        self.accept()

    def get_data(self):
        return {
            "robot_code": self.robot_code.text().strip().upper(),
            "robot_name": self.robot_name.text().strip(),
            "robot_type": self.robot_type.text().strip(),
            "area": self.area.text().strip(),
            "station": self.station.text().strip(),
            "status": self.status.currentText().strip().upper(),
            "remark": self.remark.text().strip(),
        }

    @staticmethod
    def set_combo_value(combo, value):
        normalized = str(value or "").strip().upper()
        index = combo.findText(normalized)

        if index >= 0:
            combo.setCurrentIndex(index)
