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
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from src.models.production_assignment import (
    ProductionAssignment,
)
from src.models.production_execution import (
    ProductionExecution,
)
from src.models.production_order import (
    ProductionOrder,
)
from src.services.employee_service import (
    EmployeeService,
)
from src.services.production_ng_service import (
    ProductionNGService,
)


class ProductionNGDialog(QDialog):
    MODE_ADD = "ADD"
    MODE_EDIT = "EDIT"

    TYPE_LABELS = {
        ProductionNGService.TYPE_PROCESSING: (
            "Gia công NG"
        ),
        ProductionNGService.TYPE_BLANK: (
            "Phôi NG"
        ),
    }

    def __init__(
        self,
        parent=None,
        *,
        mode="ADD",
        ng_record=None,
        session=None,
    ):
        super().__init__(parent)

        self.mode = str(
            mode or self.MODE_ADD
        ).strip().upper()

        self.ng_record = ng_record
        self.session = session

        if self.mode not in {
            self.MODE_ADD,
            self.MODE_EDIT,
        }:
            raise ValueError(
                f"Unsupported Production NG mode: {self.mode}"
            )

        if self.session is None:
            raise ValueError(
                "SQLAlchemy session is required."
            )

        if (
            self.mode == self.MODE_EDIT
            and self.ng_record is None
        ):
            raise ValueError(
                "Production NG record is required for EDIT mode."
            )

        self.employee_service = EmployeeService(
            session=self.session
        )

        self.setWindowTitle(
            (
                "Add Production NG"
                if self.mode == self.MODE_ADD
                else "Edit Production NG"
            )
        )
        self.setMinimumWidth(
            640
        )

        self.execution_combo = QComboBox(
            self
        )

        self.execution_info_label = QLabel(
            self
        )
        self.execution_info_label.setWordWrap(
            True
        )

        self.ng_type_combo = QComboBox(
            self
        )

        self.reason_combo = QComboBox(
            self
        )

        self.quantity_spin = QSpinBox(
            self
        )
        self.quantity_spin.setRange(
            1,
            2_000_000_000,
        )

        self.employee_combo = QComboBox(
            self
        )

        self.recorded_at_edit = QDateTimeEdit(
            self
        )
        self.recorded_at_edit.setCalendarPopup(
            True
        )
        self.recorded_at_edit.setDisplayFormat(
            "yyyy-MM-dd HH:mm:ss"
        )

        self.remark_edit = QTextEdit(
            self
        )
        self.remark_edit.setMaximumHeight(
            110
        )

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel,
            parent=self,
        )

        self._build_ui()
        self._connect_events()
        self._load_ng_types()
        self._load_reasons()
        self._load_employees()
        self._load_data()

    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):
        form = QFormLayout()

        form.addRow(
            "Execution *",
            self.execution_combo,
        )
        form.addRow(
            "Execution Detail",
            self.execution_info_label,
        )
        form.addRow(
            "NG Type *",
            self.ng_type_combo,
        )
        form.addRow(
            "Reason *",
            self.reason_combo,
        )
        form.addRow(
            "Quantity *",
            self.quantity_spin,
        )
        form.addRow(
            "Employee",
            self.employee_combo,
        )
        form.addRow(
            "Recorded At *",
            self.recorded_at_edit,
        )
        form.addRow(
            "Remark",
            self.remark_edit,
        )

        layout = QVBoxLayout(
            self
        )
        layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )
        layout.setSpacing(
            10
        )

        layout.addLayout(
            form
        )
        layout.addWidget(
            self.button_box
        )

    def _connect_events(self):
        self.button_box.accepted.connect(
            self._accept_if_valid
        )
        self.button_box.rejected.connect(
            self.reject
        )

        self.execution_combo.currentIndexChanged.connect(
            self._update_execution_info
        )

    # ==========================================================
    # Loading
    # ==========================================================

    def _load_ng_types(self):
        self.ng_type_combo.clear()

        for code, label in self.TYPE_LABELS.items():
            self.ng_type_combo.addItem(
                f"{label} ({code})",
                code,
            )

    def _load_reasons(self):
        self.reason_combo.clear()

        for code, name in (
            ProductionNGService.REASONS.items()
        ):
            self.reason_combo.addItem(
                f"{name} ({code})",
                code,
            )

    def _load_employees(self):
        self.employee_combo.clear()
        self.employee_combo.addItem(
            "-- Not assigned --",
            "",
        )

        for employee in (
            self.employee_service
            .get_all_employees()
        ):
            if str(
                employee.status or ""
            ).strip().upper() != "ACTIVE":
                continue

            code = str(
                employee.employee_code or ""
            ).strip().upper()

            if not code:
                continue

            name = str(
                employee.employee_name or ""
            ).strip()

            display = (
                f"{code} - {name}"
                if name
                else code
            )

            self.employee_combo.addItem(
                display,
                code,
            )

    def _load_data(self):
        self.recorded_at_edit.setDateTime(
            QDateTime.currentDateTime()
        )

        if self.mode == self.MODE_ADD:
            self._load_eligible_executions()
            self.quantity_spin.setValue(
                1
            )
            return

        self._load_existing_record()

    def _load_eligible_executions(self):
        executions = (
            self.session
            .query(ProductionExecution)
            .filter(
                ProductionExecution.status.in_(
                    [
                        "RUNNING",
                        "STOPPED",
                        "COMPLETED",
                    ]
                )
            )
            .order_by(
                ProductionExecution.start_time.desc(),
                ProductionExecution.id.desc(),
            )
            .all()
        )

        self.execution_combo.clear()

        for execution in executions:
            assignment = self._get_assignment(
                execution.assignment_id
            )

            production_order = self._get_production_order(
                assignment.production_order_id
                if assignment is not None
                else None
            )

            self.execution_combo.addItem(
                self._execution_display(
                    execution,
                    assignment,
                    production_order,
                ),
                execution.id,
            )

        self._update_execution_info()

    def _load_existing_record(self):
        execution = (
            self.session
            .query(ProductionExecution)
            .filter(
                ProductionExecution.id
                == self.ng_record.execution_id
            )
            .first()
        )

        if execution is None:
            raise ValueError(
                (
                    "Production Execution not found: "
                    f"{self.ng_record.execution_id}"
                )
            )

        assignment = self._get_assignment(
            execution.assignment_id
        )

        production_order = self._get_production_order(
            assignment.production_order_id
            if assignment is not None
            else None
        )

        self.execution_combo.clear()
        self.execution_combo.addItem(
            self._execution_display(
                execution,
                assignment,
                production_order,
            ),
            execution.id,
        )
        self.execution_combo.setEnabled(
            False
        )

        self._set_combo_data(
            self.ng_type_combo,
            self.ng_record.ng_type,
        )

        self._set_combo_data(
            self.reason_combo,
            self.ng_record.reason_code,
        )

        self.quantity_spin.setValue(
            int(
                self.ng_record.quantity
                or 1
            )
        )

        self._set_combo_data(
            self.employee_combo,
            self.ng_record.employee_code,
        )

        self.recorded_at_edit.setDateTime(
            self._to_qdatetime(
                self.ng_record.recorded_at
            )
        )

        self.remark_edit.setPlainText(
            str(
                self.ng_record.remark
                or ""
            )
        )

        self.execution_info_label.setText(
            self._execution_detail(
                execution,
                assignment,
                production_order,
            )
        )

    # ==========================================================
    # Validation
    # ==========================================================

    def _accept_if_valid(self):
        if self.execution_combo.currentData() is None:
            QMessageBox.warning(
                self,
                "Production NG",
                (
                    "No eligible Production Execution "
                    "was found."
                ),
            )
            return

        if self.ng_type_combo.currentData() is None:
            QMessageBox.warning(
                self,
                "Production NG",
                "NG Type is required.",
            )
            return

        if self.reason_combo.currentData() is None:
            QMessageBox.warning(
                self,
                "Production NG",
                "NG Reason is required.",
            )
            return

        if self.quantity_spin.value() <= 0:
            QMessageBox.warning(
                self,
                "Production NG",
                (
                    "NG Quantity must be "
                    "greater than zero."
                ),
            )
            return

        self.accept()

    # ==========================================================
    # Public data
    # ==========================================================

    def get_data(self):
        return {
            "execution_id": int(
                self.execution_combo.currentData()
            ),
            "ng_type": str(
                self.ng_type_combo.currentData()
                or ""
            ).strip().upper(),
            "reason_code": str(
                self.reason_combo.currentData()
                or ""
            ).strip().upper(),
            "quantity": (
                self.quantity_spin.value()
            ),
            "recorded_at": (
                self.recorded_at_edit
                .dateTime()
                .toString(
                    "yyyy-MM-dd HH:mm:ss"
                )
            ),
            "employee_code": str(
                self.employee_combo.currentData()
                or ""
            ).strip().upper() or None,
            "remark": (
                self.remark_edit
                .toPlainText()
                .strip()
                or None
            ),
        }

    # ==========================================================
    # Helpers
    # ==========================================================

    def _update_execution_info(
        self,
        *_,
    ):
        execution_id = (
            self.execution_combo.currentData()
        )

        if execution_id is None:
            self.execution_info_label.setText(
                "No eligible Production Execution."
            )
            return

        execution = (
            self.session
            .query(ProductionExecution)
            .filter(
                ProductionExecution.id
                == int(execution_id)
            )
            .first()
        )

        if execution is None:
            self.execution_info_label.setText(
                "Production Execution not found."
            )
            return

        assignment = self._get_assignment(
            execution.assignment_id
        )

        production_order = self._get_production_order(
            assignment.production_order_id
            if assignment is not None
            else None
        )

        self.execution_info_label.setText(
            self._execution_detail(
                execution,
                assignment,
                production_order,
            )
        )

        if (
            self.mode == self.MODE_ADD
            and assignment is not None
            and assignment.employee_code
        ):
            self._set_combo_data(
                self.employee_combo,
                assignment.employee_code,
            )

    def _get_assignment(
        self,
        assignment_id,
    ):
        if assignment_id is None:
            return None

        return (
            self.session
            .query(ProductionAssignment)
            .filter(
                ProductionAssignment.id
                == int(assignment_id)
            )
            .first()
        )

    def _get_production_order(
        self,
        production_order_id,
    ):
        if production_order_id is None:
            return None

        return (
            self.session
            .query(ProductionOrder)
            .filter(
                ProductionOrder.id
                == int(production_order_id)
            )
            .first()
        )

    @staticmethod
    def _execution_display(
        execution,
        assignment,
        production_order,
    ):
        work_order_no = (
            production_order.work_order_no
            if production_order
            else "-"
        )

        operation = (
            f"OP{production_order.operation_no}"
            if production_order
            else "-"
        )

        machine = (
            assignment.machine_code
            if assignment
            and assignment.machine_code
            else "-"
        )

        return (
            f"Execution #{execution.id} | "
            f"{work_order_no} | "
            f"{operation} | "
            f"{machine} | "
            f"{execution.status}"
        )

    @staticmethod
    def _execution_detail(
        execution,
        assignment,
        production_order,
    ):
        work_order_no = (
            production_order.work_order_no
            if production_order
            else "-"
        )

        product_code = (
            production_order.product_code
            if production_order
            else "-"
        )

        operation = (
            f"OP{production_order.operation_no}"
            if production_order
            else "-"
        )

        operation_name = (
            production_order.operation_name
            if production_order
            else "-"
        )

        machine = (
            assignment.machine_code
            if assignment
            and assignment.machine_code
            else "-"
        )

        employee = (
            assignment.employee_code
            if assignment
            and assignment.employee_code
            else "-"
        )

        shift = (
            assignment.shift
            if assignment
            and assignment.shift
            else "-"
        )

        return (
            f"Work Order: {work_order_no}\n"
            f"Product: {product_code}\n"
            f"Operation: {operation} - "
            f"{operation_name}\n"
            f"Machine: {machine}\n"
            f"Employee: {employee}\n"
            f"Shift: {shift}\n"
            f"Execution Status: {execution.status}"
        )

    @staticmethod
    def _set_combo_data(
        combo,
        value,
    ):
        normalized = str(
            value or ""
        ).strip().upper()

        index = combo.findData(
            normalized
        )

        if index >= 0:
            combo.setCurrentIndex(
                index
            )

    @staticmethod
    def _to_qdatetime(
        value,
    ):
        if value is None:
            return QDateTime.currentDateTime()

        parsed = QDateTime.fromString(
            str(value),
            "yyyy-MM-ddTHH:mm:ss",
        )

        if parsed.isValid():
            return parsed

        parsed = QDateTime.fromString(
            str(value),
            "yyyy-MM-dd HH:mm:ss",
        )

        if parsed.isValid():
            return parsed

        try:
            return QDateTime(value)
        except TypeError:
            return QDateTime.currentDateTime()
