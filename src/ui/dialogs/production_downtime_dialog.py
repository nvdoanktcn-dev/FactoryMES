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

from src.models.production_assignment import ProductionAssignment
from src.models.production_execution import ProductionExecution
from src.models.production_order import ProductionOrder
from src.services.production_downtime_service import (
    ProductionDowntimeService,
)


class ProductionDowntimeDialog(QDialog):
    MODE_START = "START"
    MODE_STOP = "STOP"

    def __init__(
        self,
        parent=None,
        *,
        mode="START",
        downtime_event=None,
        session=None,
    ):
        super().__init__(parent)

        self.mode = str(mode or self.MODE_START).strip().upper()
        self.downtime_event = downtime_event
        self.session = session

        if self.mode not in {self.MODE_START, self.MODE_STOP}:
            raise ValueError(
                f"Unsupported downtime dialog mode: {self.mode}"
            )

        if self.session is None:
            raise ValueError(
                "SQLAlchemy session is required."
            )

        self.setWindowTitle(
            "Start Production Downtime"
            if self.mode == self.MODE_START
            else "Stop Production Downtime"
        )
        self.setMinimumWidth(620)

        self.execution_combo = QComboBox(self)
        self.execution_info_label = QLabel(self)
        self.execution_info_label.setWordWrap(True)

        self.reason_combo = QComboBox(self)

        self.start_time_edit = QDateTimeEdit(self)
        self.start_time_edit.setCalendarPopup(True)
        self.start_time_edit.setDisplayFormat(
            "yyyy-MM-dd HH:mm:ss"
        )

        self.end_time_edit = QDateTimeEdit(self)
        self.end_time_edit.setCalendarPopup(True)
        self.end_time_edit.setDisplayFormat(
            "yyyy-MM-dd HH:mm:ss"
        )

        self.remark_edit = QTextEdit(self)
        self.remark_edit.setMaximumHeight(110)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel,
            parent=self,
        )

        self._build_ui()
        self._connect_events()
        self._load_reasons()
        self._load_data()
        self._apply_mode()

    def _build_ui(self):
        form = QFormLayout()
        form.addRow("Execution *", self.execution_combo)
        form.addRow(
            "Execution Detail",
            self.execution_info_label,
        )
        form.addRow(
            "Downtime Reason *",
            self.reason_combo,
        )
        form.addRow(
            "Start Time *",
            self.start_time_edit,
        )
        form.addRow(
            "End Time *",
            self.end_time_edit,
        )
        form.addRow("Remark", self.remark_edit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addLayout(form)
        layout.addWidget(self.button_box)

    def _connect_events(self):
        self.button_box.accepted.connect(
            self._accept_if_valid
        )
        self.button_box.rejected.connect(self.reject)
        self.execution_combo.currentIndexChanged.connect(
            self._update_execution_info
        )
        self.start_time_edit.dateTimeChanged.connect(
            self._sync_end_time
        )

    def _load_reasons(self):
        self.reason_combo.clear()

        for code, name in (
            ProductionDowntimeService.REASONS.items()
        ):
            self.reason_combo.addItem(
                f"{name} ({code})",
                code,
            )

    def _load_data(self):
        now = QDateTime.currentDateTime()
        self.start_time_edit.setDateTime(now)
        self.end_time_edit.setDateTime(
            now.addSecs(60)
        )

        if self.mode == self.MODE_START:
            self._load_running_executions()
        else:
            self._load_existing_event()

    def _load_running_executions(self):
        executions = (
            self.session
            .query(ProductionExecution)
            .filter(
                ProductionExecution.status
                == "RUNNING"
            )
            .order_by(
                ProductionExecution.start_time.asc(),
                ProductionExecution.id.asc(),
            )
            .all()
        )

        self.execution_combo.clear()

        for execution in executions:
            assignment = (
                self.session
                .query(ProductionAssignment)
                .filter(
                    ProductionAssignment.id
                    == execution.assignment_id
                )
                .first()
            )

            production_order = None

            if assignment is not None:
                production_order = (
                    self.session
                    .query(ProductionOrder)
                    .filter(
                        ProductionOrder.id
                        == assignment.production_order_id
                    )
                    .first()
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

    def _load_existing_event(self):
        if self.downtime_event is None:
            raise ValueError(
                "Production Downtime Event is required for STOP mode."
            )

        execution = (
            self.session
            .query(ProductionExecution)
            .filter(
                ProductionExecution.id
                == self.downtime_event.execution_id
            )
            .first()
        )

        if execution is None:
            raise ValueError(
                (
                    "Production Execution not found: "
                    f"{self.downtime_event.execution_id}"
                )
            )

        assignment = (
            self.session
            .query(ProductionAssignment)
            .filter(
                ProductionAssignment.id
                == execution.assignment_id
            )
            .first()
        )

        production_order = None

        if assignment is not None:
            production_order = (
                self.session
                .query(ProductionOrder)
                .filter(
                    ProductionOrder.id
                    == assignment.production_order_id
                )
                .first()
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
        self.execution_combo.setEnabled(False)

        reason_index = self.reason_combo.findData(
            self.downtime_event.reason_code
        )

        if reason_index >= 0:
            self.reason_combo.setCurrentIndex(
                reason_index
            )

        self.reason_combo.setEnabled(False)

        self.start_time_edit.setDateTime(
            self._to_qdatetime(
                self.downtime_event.start_time
            )
        )
        self.start_time_edit.setEnabled(False)

        self.end_time_edit.setDateTime(
            QDateTime.currentDateTime()
        )

        self.remark_edit.setPlainText(
            str(self.downtime_event.remark or "")
        )

        self.execution_info_label.setText(
            self._execution_detail(
                execution,
                assignment,
                production_order,
            )
        )

    def _apply_mode(self):
        self.end_time_edit.setEnabled(
            self.mode == self.MODE_STOP
        )

    def _accept_if_valid(self):
        if self.execution_combo.currentData() is None:
            QMessageBox.warning(
                self,
                "Production Downtime",
                "No RUNNING Production Execution was found.",
            )
            return

        if self.reason_combo.currentData() is None:
            QMessageBox.warning(
                self,
                "Production Downtime",
                "Downtime Reason is required.",
            )
            return

        if (
            self.mode == self.MODE_STOP
            and self.end_time_edit.dateTime()
            <= self.start_time_edit.dateTime()
        ):
            QMessageBox.warning(
                self,
                "Production Downtime",
                "End Time must be after Start Time.",
            )
            return

        self.accept()

    def get_data(self):
        data = {
            "execution_id": int(
                self.execution_combo.currentData()
            ),
            "reason_code": str(
                self.reason_combo.currentData()
                or ""
            ).strip().upper(),
            "start_time": (
                self.start_time_edit
                .dateTime()
                .toString(
                    "yyyy-MM-dd HH:mm:ss"
                )
            ),
            "remark": (
                self.remark_edit
                .toPlainText()
                .strip()
                or None
            ),
        }

        if self.mode == self.MODE_STOP:
            data["end_time"] = (
                self.end_time_edit
                .dateTime()
                .toString(
                    "yyyy-MM-dd HH:mm:ss"
                )
            )

        return data

    def _update_execution_info(self, *_):
        execution_id = (
            self.execution_combo.currentData()
        )

        if execution_id is None:
            self.execution_info_label.setText(
                "No eligible RUNNING Execution."
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
                "Execution not found."
            )
            return

        assignment = (
            self.session
            .query(ProductionAssignment)
            .filter(
                ProductionAssignment.id
                == execution.assignment_id
            )
            .first()
        )

        production_order = None

        if assignment is not None:
            production_order = (
                self.session
                .query(ProductionOrder)
                .filter(
                    ProductionOrder.id
                    == assignment.production_order_id
                )
                .first()
            )

        self.execution_info_label.setText(
            self._execution_detail(
                execution,
                assignment,
                production_order,
            )
        )

    def _sync_end_time(self, start_datetime):
        if (
            self.end_time_edit.dateTime()
            <= start_datetime
        ):
            self.end_time_edit.setDateTime(
                start_datetime.addSecs(60)
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
            f"{machine}"
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
            f"Operation: {operation} - {operation_name}\n"
            f"Machine: {machine}\n"
            f"Employee: {employee}\n"
            f"Shift: {shift}\n"
            f"Execution Status: {execution.status}"
        )

    @staticmethod
    def _to_qdatetime(value):
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
