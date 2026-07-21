from __future__ import annotations

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)

from src.models.production_order import ProductionOrder
from src.services.employee_service import EmployeeService
from src.services.machine_service import MachineService


class ProductionAssignmentDialog(QDialog):
    SHIFTS = ["", "DAY", "NIGHT", "OFFICE", "ROTATING"]

    def __init__(
        self,
        parent=None,
        assignment=None,
        production_order_id=None,
        session=None,
    ):
        super().__init__(parent)
        self.assignment = assignment
        self.session = session

        self.machine_service = MachineService(session=session)
        self.employee_service = EmployeeService(session=session)

        self.setWindowTitle(
            "Edit Production Assignment"
            if assignment is not None
            else "Add Production Assignment"
        )
        self.setMinimumWidth(560)

        self.production_order_combo = QComboBox(self)
        self.machine_combo = QComboBox(self)
        self.employee_combo = QComboBox(self)
        self.shift_combo = QComboBox(self)
        self.shift_combo.addItems(self.SHIFTS)

        self.planned_start_edit = QDateTimeEdit(self)
        self.planned_start_edit.setCalendarPopup(True)
        self.planned_start_edit.setDisplayFormat("yyyy-MM-dd HH:mm")

        self.planned_finish_edit = QDateTimeEdit(self)
        self.planned_finish_edit.setCalendarPopup(True)
        self.planned_finish_edit.setDisplayFormat("yyyy-MM-dd HH:mm")

        self.status_label = QLabel(self)
        self.remark_edit = QTextEdit(self)
        self.remark_edit.setMaximumHeight(100)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel,
            parent=self,
        )

        self._build_ui()
        self._connect_events()
        self._load_production_orders()
        self._load_machines()
        self._load_employees()
        self._load_assignment(production_order_id)

    def _build_ui(self):
        form = QFormLayout()
        form.addRow("Production Order *", self.production_order_combo)
        form.addRow("Machine", self.machine_combo)
        form.addRow("Employee", self.employee_combo)
        form.addRow("Shift", self.shift_combo)
        form.addRow("Planned Start", self.planned_start_edit)
        form.addRow("Planned Finish", self.planned_finish_edit)
        form.addRow("Status", self.status_label)
        form.addRow("Remark", self.remark_edit)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.button_box)

    def _connect_events(self):
        self.button_box.accepted.connect(self._accept_if_valid)
        self.button_box.rejected.connect(self.reject)
        self.planned_start_edit.dateTimeChanged.connect(self._sync_finish)

    def _load_production_orders(self):
        self.production_order_combo.clear()

        if self.session is None:
            return

        orders = (
            self.session.query(ProductionOrder)
            .order_by(
                ProductionOrder.work_order_no.asc(),
                ProductionOrder.operation_no.asc(),
            )
            .all()
        )

        for order in orders:
            display = (
                f"{order.work_order_no} / "
                f"OP{order.operation_no} / "
                f"{order.operation_name}"
            )
            self.production_order_combo.addItem(display, order.id)

    def _load_machines(self):
        self.machine_combo.clear()
        self.machine_combo.addItem("-- Not assigned --", "")

        for machine in self.machine_service.get_all_machines():
            status = str(machine.status or "").strip().upper()
            if status not in {"ACTIVE", "RUNNING"}:
                continue

            code = str(machine.machine_code or "").strip().upper()
            if not code:
                continue

            name = str(machine.machine_name or "").strip()
            display = f"{code} - {name}" if name else code
            self.machine_combo.addItem(display, code)

    def _load_employees(self):
        self.employee_combo.clear()
        self.employee_combo.addItem("-- Not assigned --", "")

        for employee in self.employee_service.get_all_employees():
            if str(employee.status or "").strip().upper() != "ACTIVE":
                continue

            code = str(employee.employee_code or "").strip().upper()
            if not code:
                continue

            name = str(employee.employee_name or "").strip()
            display = f"{code} - {name}" if name else code
            self.employee_combo.addItem(display, code)

    def _load_assignment(self, production_order_id):
        now = QDateTime.currentDateTime()
        self.planned_start_edit.setDateTime(now)
        self.planned_finish_edit.setDateTime(now.addSecs(8 * 3600))
        self.status_label.setText("DRAFT")

        target_production_order_id = production_order_id

        if self.assignment is not None:
            target_production_order_id = self.assignment.production_order_id
            self._set_combo_data(self.machine_combo, self.assignment.machine_code)
            self._set_combo_data(self.employee_combo, self.assignment.employee_code)
            self.shift_combo.setCurrentText(
                str(self.assignment.shift or "").strip().upper()
            )

            if self.assignment.planned_start:
                self.planned_start_edit.setDateTime(
                    QDateTime(self.assignment.planned_start)
                )

            if self.assignment.planned_finish:
                self.planned_finish_edit.setDateTime(
                    QDateTime(self.assignment.planned_finish)
                )

            self.status_label.setText(str(self.assignment.status or "DRAFT"))
            self.remark_edit.setPlainText(str(self.assignment.remark or ""))
            self.production_order_combo.setEnabled(False)

        if target_production_order_id is not None:
            index = self.production_order_combo.findData(int(target_production_order_id))
            if index >= 0:
                self.production_order_combo.setCurrentIndex(index)

    def _sync_finish(self, start_datetime):
        if self.planned_finish_edit.dateTime() <= start_datetime:
            self.planned_finish_edit.setDateTime(
                start_datetime.addSecs(8 * 3600)
            )

    def _accept_if_valid(self):
        if self.production_order_combo.currentData() is None:
            QMessageBox.warning(
                self,
                "Production Assignment",
                "Production Order is required.",
            )
            return

        if self.planned_finish_edit.dateTime() <= self.planned_start_edit.dateTime():
            QMessageBox.warning(
                self,
                "Production Assignment",
                "Planned Finish must be after Planned Start.",
            )
            return

        self.accept()

    def get_data(self):
        return {
            "production_order_id": int(self.production_order_combo.currentData()),
            "machine_code": str(self.machine_combo.currentData() or "").strip().upper() or None,
            "employee_code": str(self.employee_combo.currentData() or "").strip().upper() or None,
            "shift": str(self.shift_combo.currentText() or "").strip().upper() or None,
            "planned_start": self.planned_start_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            "planned_finish": self.planned_finish_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            "status": str(
                self.assignment.status if self.assignment is not None else "DRAFT"
            ).strip().upper(),
            "remark": self.remark_edit.toPlainText().strip() or None,
        }

    @staticmethod
    def _set_combo_data(combo, value):
        normalized = str(value or "").strip().upper()
        index = combo.findData(normalized)
        if index >= 0:
            combo.setCurrentIndex(index)
