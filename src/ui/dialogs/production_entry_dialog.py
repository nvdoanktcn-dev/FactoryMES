from datetime import datetime, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from src.services.production_entry_lookup_service import (
    ProductionEntryLookupService,
)
from src.services.production_execution_service import (
    ProductionExecutionService,
)
from src.ui.widgets.datetime_picker import (
    DateTimePicker,
)
from src.ui.widgets.lookup_combo_box import (
    LookupComboBox,
)
from src.ui.widgets.production_kpi_widget import (
    ProductionKPIWidget,
)
from src.ui.widgets.warning_panel import (
    WarningPanel,
)


class ProductionEntryDialog(QDialog):
    """
    Production Entry Dialog V2.

    Luồng:
        Work Order
            -> Product
            -> Routing OP
            -> Machine phù hợp
            -> Employee ACTIVE
            -> Preview KPI
            -> Save Production Log
            -> Update Work Order Progress
    """

    SHIFTS = [
        "DAY",
        "NIGHT",
    ]

    DOWNTIME_REASONS = [
        "",
        "WAITING OPERATOR",
        "WAITING MATERIAL",
        "WAITING ORDER",
        "MAINTENANCE",
        "POWER OUTAGE",
        "MACHINE REPAIR",
        "TOOL CHANGE",
        "CLEANING",
        "PROGRAMMING",
        "OTHER",
    ]

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.lookup_service = (
            ProductionEntryLookupService()
        )

        self.execution_service = (
            ProductionExecutionService()
        )

        self.last_engine_result = None
        self.last_execution_result = None

        self.setWindowTitle(
            "Production Entry"
        )
        self.resize(
            980,
            760,
        )

        self.work_order_combo = (
            LookupComboBox(
                placeholder=(
                    "-- Select Work Order --"
                )
            )
        )

        self.product_value = QLabel("-")
        self.status_value = QLabel("-")
        self.plan_qty_value = QLabel("0")
        self.completed_qty_value = QLabel("0")
        self.remaining_qty_value = QLabel("0")

        self.op_combo = LookupComboBox(
            placeholder="-- Select Operation --"
        )

        self.machine_combo = LookupComboBox(
            placeholder="-- Select Machine --"
        )

        self.employee_combo = LookupComboBox(
            placeholder="-- Select Employee --"
        )

        self.shift_combo = QComboBox()
        self.shift_combo.addItems(
            self.SHIFTS
        )

        now = datetime.now()
        default_start = now.replace(
            minute=0,
            second=0,
            microsecond=0,
        )

        self.start_time = DateTimePicker(
            value=default_start
        )

        self.finish_time = DateTimePicker(
            value=default_start
            + timedelta(hours=1)
        )

        self.ok_qty = QSpinBox()
        self.ok_qty.setRange(
            0,
            999999999,
        )

        self.ng_qty = QSpinBox()
        self.ng_qty.setRange(
            0,
            999999999,
        )

        self.downtime_min = QDoubleSpinBox()
        self.downtime_min.setRange(
            0.0,
            99999.0,
        )
        self.downtime_min.setDecimals(2)
        self.downtime_min.setSuffix(
            " min"
        )

        self.downtime_reason = QComboBox()
        self.downtime_reason.addItems(
            self.DOWNTIME_REASONS
        )

        self.remark = QTextEdit()
        self.remark.setMaximumHeight(80)

        self.kpi_widget = (
            ProductionKPIWidget()
        )

        self.warning_panel = (
            WarningPanel()
        )

        self.btn_preview = QPushButton(
            "Preview"
        )
        self.btn_save = QPushButton(
            "Save"
        )
        self.btn_clear = QPushButton(
            "Clear"
        )
        self.btn_cancel = QPushButton(
            "Cancel"
        )

        self.build_ui()
        self.connect_events()
        self.load_initial_data()

    # ==========================================================
    # UI
    # ==========================================================

    def build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setSpacing(12)

        title = QLabel(
            "Production Execution"
        )
        title.setAlignment(
            Qt.AlignCenter
        )
        title.setStyleSheet(
            "font-size:20px;"
            "font-weight:bold;"
        )

        master_group = QGroupBox(
            "Production Context"
        )
        master_layout = QGridLayout(
            master_group
        )

        master_layout.addWidget(
            QLabel("Work Order *"),
            0,
            0,
        )
        master_layout.addWidget(
            self.work_order_combo,
            0,
            1,
        )

        master_layout.addWidget(
            QLabel("Product"),
            0,
            2,
        )
        master_layout.addWidget(
            self.product_value,
            0,
            3,
        )

        master_layout.addWidget(
            QLabel("WO Status"),
            1,
            0,
        )
        master_layout.addWidget(
            self.status_value,
            1,
            1,
        )

        master_layout.addWidget(
            QLabel("Plan Qty"),
            1,
            2,
        )
        master_layout.addWidget(
            self.plan_qty_value,
            1,
            3,
        )

        master_layout.addWidget(
            QLabel("Completed Qty"),
            2,
            0,
        )
        master_layout.addWidget(
            self.completed_qty_value,
            2,
            1,
        )

        master_layout.addWidget(
            QLabel("Remaining Qty"),
            2,
            2,
        )
        master_layout.addWidget(
            self.remaining_qty_value,
            2,
            3,
        )

        operation_group = QGroupBox(
            "Operation"
        )
        operation_form = QFormLayout(
            operation_group
        )

        operation_form.addRow(
            "Operation *",
            self.op_combo,
        )
        operation_form.addRow(
            "Machine *",
            self.machine_combo,
        )
        operation_form.addRow(
            "Employee *",
            self.employee_combo,
        )
        operation_form.addRow(
            "Shift",
            self.shift_combo,
        )

        quantity_group = QGroupBox(
            "Production Data"
        )
        quantity_form = QFormLayout(
            quantity_group
        )

        quantity_form.addRow(
            "Start Time *",
            self.start_time,
        )
        quantity_form.addRow(
            "Finish Time *",
            self.finish_time,
        )
        quantity_form.addRow(
            "OK Qty",
            self.ok_qty,
        )
        quantity_form.addRow(
            "NG Qty",
            self.ng_qty,
        )
        quantity_form.addRow(
            "Downtime",
            self.downtime_min,
        )
        quantity_form.addRow(
            "Downtime Reason",
            self.downtime_reason,
        )
        quantity_form.addRow(
            "Remark",
            self.remark,
        )

        middle_layout = QHBoxLayout()
        middle_layout.addWidget(
            operation_group,
            1,
        )
        middle_layout.addWidget(
            quantity_group,
            1,
        )

        result_layout = QHBoxLayout()
        result_layout.addWidget(
            self.kpi_widget,
            1,
        )
        result_layout.addWidget(
            self.warning_panel,
            1,
        )

        button_layout = QHBoxLayout()
        button_layout.addWidget(
            self.btn_preview
        )
        button_layout.addStretch()
        button_layout.addWidget(
            self.btn_save
        )
        button_layout.addWidget(
            self.btn_clear
        )
        button_layout.addWidget(
            self.btn_cancel
        )

        root_layout.addWidget(title)
        root_layout.addWidget(
            master_group
        )
        root_layout.addLayout(
            middle_layout
        )
        root_layout.addLayout(
            result_layout
        )
        root_layout.addLayout(
            button_layout
        )

    # ==========================================================
    # Events
    # ==========================================================

    def connect_events(self):
        self.work_order_combo.value_changed.connect(
            self.on_work_order_changed
        )

        self.op_combo.value_changed.connect(
            self.on_operation_changed
        )

        self.btn_preview.clicked.connect(
            self.preview_entry
        )

        self.btn_save.clicked.connect(
            self.save_entry
        )

        self.btn_clear.clicked.connect(
            self.clear_form
        )

        self.btn_cancel.clicked.connect(
            self.reject
        )

    # ==========================================================
    # Initial data
    # ==========================================================

    def load_initial_data(self):
        self.load_work_orders()
        self.load_employees()

        self.op_combo.clear_items()
        self.machine_combo.clear_items()

        self.kpi_widget.clear_values()
        self.warning_panel.clear_messages()

    def load_work_orders(self):
        work_orders = (
            self.lookup_service
            .get_available_work_orders()
        )

        self.work_order_combo.set_items(
            work_orders,
            key_getter=lambda item:
                item.work_order_no,
            text_getter=lambda item:
                (
                    f"{item.work_order_no} - "
                    f"{item.product_code} - "
                    f"{item.status}"
                ),
        )

    def load_employees(self):
        employees = (
            self.lookup_service
            .get_active_employees()
        )

        self.employee_combo.set_items(
            employees,
            key_getter=lambda item:
                item.employee_code,
            text_getter=lambda item:
                (
                    f"{item.employee_code} - "
                    f"{item.employee_name}"
                ),
        )

    # ==========================================================
    # Work Order
    # ==========================================================

    def on_work_order_changed(
        self,
        work_order_no,
    ):
        self.last_engine_result = None
        self.kpi_widget.clear_values()
        self.warning_panel.clear_messages()

        if not work_order_no:
            self.clear_work_order_context()
            return

        try:
            context = (
                self.lookup_service
                .build_entry_context(
                    work_order_no
                )
            )

            work_order = context[
                "work_order"
            ]

            plan_qty = int(
                work_order.plan_qty or 0
            )

            completed_qty = int(
                work_order.completed_qty or 0
            )

            remaining_qty = max(
                plan_qty - completed_qty,
                0,
            )

            self.product_value.setText(
                context["product_code"]
            )

            self.status_value.setText(
                work_order.status or ""
            )

            self.plan_qty_value.setText(
                str(plan_qty)
            )

            self.completed_qty_value.setText(
                str(completed_qty)
            )

            self.remaining_qty_value.setText(
                str(remaining_qty)
            )

            self.op_combo.set_items(
                context["routings"],
                key_getter=lambda item:
                    item.op_no,
                text_getter=lambda item:
                    (
                        f"{item.op_no} - "
                        f"{item.op_name or ''} - "
                        f"{item.machine_code or item.machine_type or ''}"
                    ),
            )

            self.machine_combo.clear_items()

        except Exception as error:
            self.clear_work_order_context()

            QMessageBox.warning(
                self,
                "Work Order",
                str(error),
            )

    def clear_work_order_context(self):
        self.product_value.setText("-")
        self.status_value.setText("-")
        self.plan_qty_value.setText("0")
        self.completed_qty_value.setText(
            "0"
        )
        self.remaining_qty_value.setText(
            "0"
        )

        self.op_combo.clear_items()
        self.machine_combo.clear_items()

    # ==========================================================
    # Operation / Machine
    # ==========================================================

    def on_operation_changed(
        self,
        op_no,
    ):
        self.last_engine_result = None
        self.kpi_widget.clear_values()
        self.warning_panel.clear_messages()

        work_order_no = (
            self.work_order_combo
            .current_value()
        )

        if not work_order_no or not op_no:
            self.machine_combo.clear_items()
            return

        try:
            machines = (
                self.lookup_service
                .get_machines_for_operation(
                    work_order_no,
                    op_no,
                )
            )

            self.machine_combo.set_items(
                machines,
                key_getter=lambda item:
                    item.machine_code,
                text_getter=lambda item:
                    (
                        f"{item.machine_code} - "
                        f"{item.machine_name or ''} - "
                        f"{item.machine_type or ''}"
                    ),
            )

            if not machines:
                QMessageBox.warning(
                    self,
                    "Machine",
                    (
                        "No active Machine is available "
                        f"for operation {op_no}."
                    ),
                )

        except Exception as error:
            self.machine_combo.clear_items()

            QMessageBox.warning(
                self,
                "Operation",
                str(error),
            )

    # ==========================================================
    # Data
    # ==========================================================

    def get_data(self):
        work_order_no = (
            self.work_order_combo
            .require_value(
                "Work Order"
            )
        )

        op_no = (
            self.op_combo
            .require_value(
                "Operation"
            )
        )

        machine_code = (
            self.machine_combo
            .require_value(
                "Machine"
            )
        )

        employee_code = (
            self.employee_combo
            .require_value(
                "Employee"
            )
        )

        product_code = str(
            self.product_value.text()
            or ""
        ).strip().upper()

        start_time = (
            self.start_time.value()
        )

        finish_time = (
            self.finish_time.value()
        )

        if finish_time <= start_time:
            raise ValueError(
                "Finish Time must be later "
                "than Start Time."
            )

        ok_qty = self.ok_qty.value()
        ng_qty = self.ng_qty.value()

        if ok_qty + ng_qty <= 0:
            raise ValueError(
                "OK Qty + NG Qty must be "
                "greater than zero."
            )

        return {
            "work_order_no":
                work_order_no,

            "product_code":
                product_code,

            "op_no":
                op_no,

            "machine_code":
                machine_code,

            "employee_code":
                employee_code,

            "shift":
                self.shift_combo
                .currentText()
                .strip()
                .upper(),

            "start_time":
                start_time,

            "finish_time":
                finish_time,

            "run_time_sec":
                0,

            "ok_qty":
                ok_qty,

            "ng_qty":
                ng_qty,

            "downtime_min":
                self.downtime_min
                .value(),

            "downtime_reason":
                self.downtime_reason
                .currentText()
                .strip()
                .upper(),

            "status":
                "COMPLETED",

            "remark":
                self.remark
                .toPlainText()
                .strip(),
        }

    # ==========================================================
    # Preview
    # ==========================================================

    def preview_entry(self):
        try:
            data = self.get_data()

            engine_result = (
                self.execution_service
                .validate_entry(data)
            )

            self.last_engine_result = (
                engine_result
            )

            self.warning_panel.set_engine_result(
                engine_result
            )

            self.kpi_widget.set_calculation(
                engine_result.calculation
            )

            if engine_result.is_valid:
                QMessageBox.information(
                    self,
                    "Production Preview",
                    (
                        "Production Entry is valid."
                        "\nReview KPI and warnings "
                        "before saving."
                    ),
                )

        except Exception as error:
            self.last_engine_result = None
            self.kpi_widget.clear_values()

            QMessageBox.warning(
                self,
                "Production Preview",
                str(error),
            )

    # ==========================================================
    # Save
    # ==========================================================

    def save_entry(self):
        try:
            data = self.get_data()

            result = (
                self.execution_service
                .execute(
                    data=data,
                    allow_warnings=True,
                    update_work_order=True,
                )
            )

            self.last_execution_result = (
                result
            )

            self.warning_panel.set_engine_result(
                result.engine_result
            )

            self.kpi_widget.set_calculation(
                result.engine_result
                .calculation
            )

            if not result.saved:
                error_text = "\n".join(
                    (
                        f"[{item.code}] "
                        f"{item.message}"
                    )
                    for item in result.errors
                )

                if not error_text:
                    error_text = (
                        "Production Entry was not saved."
                    )

                QMessageBox.warning(
                    self,
                    "Production Entry",
                    error_text,
                )
                return

            calculation = (
                result.engine_result
                .calculation
            )

            message = (
                "Production Log saved successfully."
                f"\n\nOK Qty: {calculation.ok_qty}"
                f"\nNG Qty: {calculation.ng_qty}"
                f"\nYield: "
                f"{calculation.yield_percent:.2f}%"
                f"\nPerformance: "
                f"{calculation.performance_percent:.2f}%"
            )

            if (
                result.progress_result
                is not None
            ):
                progress = (
                    result.progress_result
                )

                message += (
                    f"\n\nWO Progress: "
                    f"{progress.progress_percent:.2f}%"
                    f"\nRemaining Qty: "
                    f"{progress.remaining_qty}"
                    f"\nWO Status: "
                    f"{progress.suggested_status}"
                )

            QMessageBox.information(
                self,
                "Production Entry",
                message,
            )

            self.accept()

        except Exception as error:
            QMessageBox.warning(
                self,
                "Production Entry Error",
                str(error),
            )

    # ==========================================================
    # Clear
    # ==========================================================

    def clear_form(self):
        self.ok_qty.setValue(0)
        self.ng_qty.setValue(0)
        self.downtime_min.setValue(
            0.0
        )
        self.downtime_reason.setCurrentIndex(
            0
        )
        self.remark.clear()

        now = datetime.now().replace(
            minute=0,
            second=0,
            microsecond=0,
        )

        self.start_time.set_value(now)
        self.finish_time.set_value(
            now + timedelta(hours=1)
        )

        self.last_engine_result = None
        self.last_execution_result = None

        self.kpi_widget.clear_values()
        self.warning_panel.clear_messages()