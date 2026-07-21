from __future__ import annotations

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from src.models.production_assignment import ProductionAssignment
from src.models.production_order import ProductionOrder


class ProductionExecutionDialog(QDialog):
    MODE_START = "START"
    MODE_STOP = "STOP"
    MODE_COMPLETE = "COMPLETE"

    def __init__(
        self,
        parent=None,
        *,
        mode="START",
        execution=None,
        session=None,
    ):
        super().__init__(parent)

        self.mode = str(mode or self.MODE_START).strip().upper()
        self.execution = execution
        self.session = session

        if self.mode not in {
            self.MODE_START,
            self.MODE_STOP,
            self.MODE_COMPLETE,
        }:
            raise ValueError(
                f"Unsupported execution dialog mode: {self.mode}"
            )

        if self.session is None:
            raise ValueError(
                "SQLAlchemy session is required."
            )

        self.setWindowTitle(
            self._window_title()
        )
        self.setMinimumWidth(580)

        self.assignment_combo = QComboBox(self)
        self.assignment_info_label = QLabel(self)
        self.assignment_info_label.setWordWrap(True)

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

        self.ok_qty_spin = QSpinBox(self)
        self.ok_qty_spin.setRange(0, 2_000_000_000)

        self.ng_qty_spin = QSpinBox(self)
        self.ng_qty_spin.setRange(0, 2_000_000_000)

        self.processing_ng_spin = QSpinBox(self)
        self.processing_ng_spin.setRange(0, 2_000_000_000)

        self.blank_ng_spin = QSpinBox(self)
        self.blank_ng_spin.setRange(0, 2_000_000_000)

        self.downtime_spin = QDoubleSpinBox(self)
        self.downtime_spin.setRange(0.0, 1_000_000.0)
        self.downtime_spin.setDecimals(2)
        self.downtime_spin.setSuffix(" min")

        self.remark_edit = QTextEdit(self)
        self.remark_edit.setMaximumHeight(110)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel,
            parent=self,
        )

        self._build_ui()
        self._connect_events()
        self._load_data()
        self._apply_mode()

    def _build_ui(self):
        form = QFormLayout()
        form.addRow(
            "Assignment *",
            self.assignment_combo,
        )
        form.addRow(
            "Assignment Detail",
            self.assignment_info_label,
        )
        form.addRow(
            "Start Time *",
            self.start_time_edit,
        )
        form.addRow(
            "End Time *",
            self.end_time_edit,
        )
        form.addRow(
            "OK Qty",
            self.ok_qty_spin,
        )
        form.addRow(
            "Total NG",
            self.ng_qty_spin,
        )
        form.addRow(
            "Processing NG",
            self.processing_ng_spin,
        )
        form.addRow(
            "Blank NG",
            self.blank_ng_spin,
        )
        form.addRow(
            "Downtime",
            self.downtime_spin,
        )
        form.addRow(
            "Remark",
            self.remark_edit,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )
        layout.setSpacing(10)
        layout.addLayout(form)
        layout.addWidget(self.button_box)

    def _connect_events(self):
        self.button_box.accepted.connect(
            self._accept_if_valid
        )
        self.button_box.rejected.connect(
            self.reject
        )
        self.assignment_combo.currentIndexChanged.connect(
            self._update_assignment_info
        )
        self.start_time_edit.dateTimeChanged.connect(
            self._sync_end_time
        )
        self.processing_ng_spin.valueChanged.connect(
            self._sync_total_ng
        )
        self.blank_ng_spin.valueChanged.connect(
            self._sync_total_ng
        )

    def _load_data(self):
        now = QDateTime.currentDateTime()
        self.start_time_edit.setDateTime(now)
        self.end_time_edit.setDateTime(
            now.addSecs(60)
        )

        if self.mode == self.MODE_START:
            self._load_start_assignments()
        else:
            self._load_execution_assignment()

    def _load_start_assignments(self):
        assignments = (
            self.session
            .query(ProductionAssignment)
            .filter(
                ProductionAssignment.status
                == "IN_PROGRESS"
            )
            .order_by(
                ProductionAssignment.planned_start.asc(),
                ProductionAssignment.id.asc(),
            )
            .all()
        )

        self.assignment_combo.clear()

        for assignment in assignments:
            production_order = (
                self.session
                .query(ProductionOrder)
                .filter(
                    ProductionOrder.id
                    == assignment.production_order_id
                )
                .first()
            )

            self.assignment_combo.addItem(
                self._assignment_display(
                    assignment,
                    production_order,
                ),
                assignment.id,
            )

        self._update_assignment_info()

    def _load_execution_assignment(self):
        if self.execution is None:
            raise ValueError(
                (
                    "Production Execution is required "
                    f"for {self.mode} mode."
                )
            )

        assignment = (
            self.session
            .query(ProductionAssignment)
            .filter(
                ProductionAssignment.id
                == self.execution.assignment_id
            )
            .first()
        )

        if assignment is None:
            raise ValueError(
                (
                    "Production Assignment not found: "
                    f"{self.execution.assignment_id}"
                )
            )

        production_order = (
            self.session
            .query(ProductionOrder)
            .filter(
                ProductionOrder.id
                == assignment.production_order_id
            )
            .first()
        )

        self.assignment_combo.clear()
        self.assignment_combo.addItem(
            self._assignment_display(
                assignment,
                production_order,
            ),
            assignment.id,
        )
        self.assignment_combo.setEnabled(False)

        self.start_time_edit.setDateTime(
            self._to_qdatetime(
                self.execution.start_time
            )
        )
        self.end_time_edit.setDateTime(
            QDateTime.currentDateTime()
        )

        self.ok_qty_spin.setValue(
            int(self.execution.ok_qty or 0)
        )
        self.ng_qty_spin.setValue(
            int(self.execution.ng_qty or 0)
        )
        self.processing_ng_spin.setValue(
            int(
                self.execution.processing_ng_qty
                or 0
            )
        )
        self.blank_ng_spin.setValue(
            int(self.execution.blank_ng_qty or 0)
        )
        self.downtime_spin.setValue(
            float(
                self.execution.downtime_minutes
                or 0.0
            )
        )
        self.remark_edit.setPlainText(
            str(self.execution.remark or "")
        )

        self.assignment_info_label.setText(
            self._assignment_detail(
                assignment,
                production_order,
            )
        )

    def _apply_mode(self):
        is_start = self.mode == self.MODE_START

        self.end_time_edit.setEnabled(
            not is_start
        )

        for widget in (
            self.ok_qty_spin,
            self.ng_qty_spin,
            self.processing_ng_spin,
            self.blank_ng_spin,
            self.downtime_spin,
        ):
            widget.setEnabled(
                not is_start
            )

    def _accept_if_valid(self):
        if self.assignment_combo.currentData() is None:
            QMessageBox.warning(
                self,
                "Production Execution",
                (
                    "No eligible IN_PROGRESS "
                    "Assignment was found."
                ),
            )
            return

        if (
            self.mode != self.MODE_START
            and self.end_time_edit.dateTime()
            <= self.start_time_edit.dateTime()
        ):
            QMessageBox.warning(
                self,
                "Production Execution",
                "End Time must be after Start Time.",
            )
            return

        categorized_ng = (
            self.processing_ng_spin.value()
            + self.blank_ng_spin.value()
        )

        if categorized_ng > self.ng_qty_spin.value():
            QMessageBox.warning(
                self,
                "Production Execution",
                (
                    "Processing NG + Blank NG "
                    "cannot exceed Total NG."
                ),
            )
            return

        if self.mode != self.MODE_START:
            elapsed_minutes = (
                self.start_time_edit
                .dateTime()
                .secsTo(
                    self.end_time_edit.dateTime()
                )
                / 60.0
            )

            if (
                self.downtime_spin.value()
                > elapsed_minutes
            ):
                QMessageBox.warning(
                    self,
                    "Production Execution",
                    (
                        "Downtime cannot exceed "
                        "total elapsed time."
                    ),
                )
                return

        self.accept()

    def get_data(self):
        data = {
            "assignment_id": int(
                self.assignment_combo.currentData()
            ),
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

        if self.mode != self.MODE_START:
            data.update(
                {
                    "end_time": (
                        self.end_time_edit
                        .dateTime()
                        .toString(
                            "yyyy-MM-dd HH:mm:ss"
                        )
                    ),
                    "ok_qty": self.ok_qty_spin.value(),
                    "ng_qty": self.ng_qty_spin.value(),
                    "processing_ng_qty": (
                        self.processing_ng_spin.value()
                    ),
                    "blank_ng_qty": (
                        self.blank_ng_spin.value()
                    ),
                    "downtime_minutes": (
                        self.downtime_spin.value()
                    ),
                    "complete": (
                        self.mode
                        == self.MODE_COMPLETE
                    ),
                }
            )

        return data

    def _update_assignment_info(
        self,
        *_,
    ):
        assignment_id = (
            self.assignment_combo.currentData()
        )

        if assignment_id is None:
            self.assignment_info_label.setText(
                "No eligible Assignment."
            )
            return

        assignment = (
            self.session
            .query(ProductionAssignment)
            .filter(
                ProductionAssignment.id
                == int(assignment_id)
            )
            .first()
        )

        if assignment is None:
            self.assignment_info_label.setText(
                "Assignment not found."
            )
            return

        production_order = (
            self.session
            .query(ProductionOrder)
            .filter(
                ProductionOrder.id
                == assignment.production_order_id
            )
            .first()
        )

        self.assignment_info_label.setText(
            self._assignment_detail(
                assignment,
                production_order,
            )
        )

    def _sync_end_time(
        self,
        start_datetime,
    ):
        if (
            self.end_time_edit.dateTime()
            <= start_datetime
        ):
            self.end_time_edit.setDateTime(
                start_datetime.addSecs(60)
            )

    def _sync_total_ng(
        self,
        *_,
    ):
        categorized_ng = (
            self.processing_ng_spin.value()
            + self.blank_ng_spin.value()
        )

        if categorized_ng > self.ng_qty_spin.value():
            self.ng_qty_spin.setValue(
                categorized_ng
            )

    @staticmethod
    def _assignment_display(
        assignment,
        production_order,
    ):
        if production_order is None:
            return f"Assignment #{assignment.id}"

        return (
            f"#{assignment.id} | "
            f"{production_order.work_order_no} | "
            f"OP{production_order.operation_no} | "
            f"{production_order.operation_name}"
        )

    @staticmethod
    def _assignment_detail(
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

        return (
            f"Work Order: {work_order_no}\\n"
            f"Operation: {operation}\\n"
            f"Machine: {assignment.machine_code or '-'}\\n"
            f"Employee: {assignment.employee_code or '-'}\\n"
            f"Shift: {assignment.shift or '-'}"
        )

    def _window_title(self):
        titles = {
            self.MODE_START: "Start Production Execution",
            self.MODE_STOP: "Stop Production Execution",
            self.MODE_COMPLETE: (
                "Complete Production Execution"
            ),
        }
        return titles[self.mode]

    @staticmethod
    def _to_qdatetime(
        value,
    ):
        if value is None:
            return QDateTime.currentDateTime()

        if isinstance(value, QDateTime):
            return value

        parsed = QDateTime.fromString(
            str(value),
            Qt.ISODate,
        )

        if parsed.isValid():
            return parsed

        try:
            return QDateTime(value)
        except TypeError:
            return QDateTime.currentDateTime()
