from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QLineEdit, QMessageBox, QSpinBox,
    QTextEdit, QVBoxLayout,
)


class RoutingDialog(QDialog):
    PROCESS_TYPES = ["CNC", "ROBOT", "MANUAL", "INSPECTION", "OTHER"]
    STATUSES = ["ACTIVE", "INACTIVE"]

    def __init__(self, parent=None, routing=None):
        super().__init__(parent)
        self.routing = routing
        self.setWindowTitle("Edit Routing" if routing else "Add Routing")
        self.setMinimumWidth(520)

        self.product_code_edit = QLineEdit(self)
        self.operation_no_spin = QSpinBox(self)
        self.operation_no_spin.setRange(1, 999999)
        self.operation_no_spin.setSingleStep(10)
        self.operation_name_edit = QLineEdit(self)

        self.process_type_combo = QComboBox(self)
        self.process_type_combo.addItems(self.PROCESS_TYPES)
        self.machine_type_edit = QLineEdit(self)

        self.cycle_time_spin = QDoubleSpinBox(self)
        self.cycle_time_spin.setRange(0.000001, 999999999.0)
        self.cycle_time_spin.setDecimals(6)

        self.output_spin = QDoubleSpinBox(self)
        self.output_spin.setRange(0.0, 999999999.0)
        self.output_spin.setDecimals(4)

        self.operator_count_spin = QDoubleSpinBox(self)
        self.operator_count_spin.setRange(0.000001, 9999.0)
        self.operator_count_spin.setDecimals(2)
        self.operator_count_spin.setValue(1.0)

        self.status_combo = QComboBox(self)
        self.status_combo.addItems(self.STATUSES)
        self.remark_edit = QTextEdit(self)
        self.remark_edit.setMaximumHeight(100)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel,
            parent=self,
        )

        form = QFormLayout()
        form.addRow("Product Code *", self.product_code_edit)
        form.addRow("Operation No *", self.operation_no_spin)
        form.addRow("Operation Name *", self.operation_name_edit)
        form.addRow("Process Type *", self.process_type_combo)
        form.addRow("Machine Type", self.machine_type_edit)
        form.addRow("Standard Cycle Time (Sec) *", self.cycle_time_spin)
        form.addRow("Standard Output (PCS/H)", self.output_spin)
        form.addRow("Standard Operator Count", self.operator_count_spin)
        form.addRow("Status", self.status_combo)
        form.addRow("Remark", self.remark_edit)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self._accept_if_valid)
        self.button_box.rejected.connect(self.reject)
        self._load_routing()

    def _load_routing(self):
        if self.routing is None:
            self.operation_no_spin.setValue(10)
            self.cycle_time_spin.setValue(1.0)
            return

        self.product_code_edit.setText(str(self.routing.product_code or ""))
        self.operation_no_spin.setValue(int(self.routing.operation_no or 1))
        self.operation_name_edit.setText(str(self.routing.operation_name or ""))
        self.process_type_combo.setCurrentText(str(self.routing.process_type or "CNC").upper())
        self.machine_type_edit.setText(str(self.routing.machine_type or ""))
        self.cycle_time_spin.setValue(float(self.routing.standard_cycle_time_sec or 0.000001))
        self.output_spin.setValue(float(self.routing.standard_output_pcs_hour or 0.0))
        self.operator_count_spin.setValue(float(self.routing.standard_operator_count or 1.0))
        self.status_combo.setCurrentText(str(self.routing.status or "ACTIVE").upper())
        self.remark_edit.setPlainText(str(self.routing.remark or ""))

        self.product_code_edit.setReadOnly(True)
        self.operation_no_spin.setEnabled(False)

    def _accept_if_valid(self):
        if not self.product_code_edit.text().strip():
            QMessageBox.warning(self, "Routing", "Product Code is required.")
            return
        if not self.operation_name_edit.text().strip():
            QMessageBox.warning(self, "Routing", "Operation Name is required.")
            return
        if self.cycle_time_spin.value() <= 0:
            QMessageBox.warning(self, "Routing", "Standard Cycle Time must be greater than zero.")
            return
        self.accept()

    def get_data(self):
        return {
            "product_code": self.product_code_edit.text().strip().upper(),
            "operation_no": self.operation_no_spin.value(),
            "operation_name": self.operation_name_edit.text().strip(),
            "process_type": self.process_type_combo.currentText().strip().upper(),
            "machine_type": self.machine_type_edit.text().strip().upper() or None,
            "standard_cycle_time_sec": self.cycle_time_spin.value(),
            "standard_output_pcs_hour": self.output_spin.value(),
            "standard_operator_count": self.operator_count_spin.value(),
            "status": self.status_combo.currentText().strip().upper(),
            "remark": self.remark_edit.toPlainText().strip() or None,
        }
