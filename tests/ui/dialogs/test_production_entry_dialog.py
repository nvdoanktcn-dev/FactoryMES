from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from tests.base.qt_test_case import QtTestCase

from src.ui.dialogs.production_entry_dialog import (
    ProductionEntryDialog,
)


def make_work_order(
    *,
    work_order_no: str = "WO001",
    product_code: str = "P001",
    status: str = "RUNNING",
    plan_qty: int = 100,
    completed_qty: int = 40,
):
    return SimpleNamespace(
        work_order_no=work_order_no,
        product_code=product_code,
        status=status,
        plan_qty=plan_qty,
        completed_qty=completed_qty,
    )


def make_routing(
    *,
    op_no: str = "OP10",
    op_name: str = "Turning",
    machine_code: str = "BL01",
    machine_type: str = "CNC",
):
    return SimpleNamespace(
        op_no=op_no,
        op_name=op_name,
        machine_code=machine_code,
        machine_type=machine_type,
    )


def make_machine(
    *,
    machine_code: str = "BL01",
    machine_name: str = "CNC 01",
    machine_type: str = "CNC",
):
    return SimpleNamespace(
        machine_code=machine_code,
        machine_name=machine_name,
        machine_type=machine_type,
    )


def make_employee(
    *,
    employee_code: str = "E001",
    employee_name: str = "Operator 01",
):
    return SimpleNamespace(
        employee_code=employee_code,
        employee_name=employee_name,
    )


class TestProductionEntryDialog(QtTestCase):

    def setUp(self) -> None:
        super().setUp()

        lookup_patcher = patch(
            "src.ui.dialogs.production_entry_dialog."
            "ProductionEntryLookupService"
        )
        execution_patcher = patch(
            "src.ui.dialogs.production_entry_dialog."
            "ProductionExecutionService"
        )

        self.addCleanup(lookup_patcher.stop)
        self.addCleanup(execution_patcher.stop)

        lookup_class = lookup_patcher.start()
        execution_class = execution_patcher.start()

        self.lookup_service = lookup_class.return_value
        self.execution_service = execution_class.return_value

        self.lookup_service.get_available_work_orders.return_value = []
        self.lookup_service.get_active_employees.return_value = []

        self.dialog = ProductionEntryDialog()
        self.process_events()

    def tearDown(self) -> None:
        self.dispose_widget(self.dialog)
        super().tearDown()

    # ==========================================================
    # Creation / initial data
    # ==========================================================

    def test_dialog_created(self) -> None:
        self.assertEqual(
            self.dialog.windowTitle(),
            "Production Entry",
        )

        self.assertIs(
            self.dialog.lookup_service,
            self.lookup_service,
        )
        self.assertIs(
            self.dialog.execution_service,
            self.execution_service,
        )

    def test_initial_data_loaded(self) -> None:
        self.lookup_service.get_available_work_orders.assert_called_once_with()
        self.lookup_service.get_active_employees.assert_called_once_with()

        self.assertEqual(
            self.dialog.product_value.text(),
            "-",
        )
        self.assertEqual(
            self.dialog.status_value.text(),
            "-",
        )

    # ==========================================================
    # Work Order
    # ==========================================================

    def test_work_order_change_updates_context(self) -> None:
        work_order = make_work_order(
            plan_qty=120,
            completed_qty=45,
        )
        routings = [
            make_routing(
                op_no="OP10",
                machine_code="BL01",
            ),
            make_routing(
                op_no="OP20",
                machine_code="BL02",
            ),
        ]

        self.lookup_service.build_entry_context.return_value = {
            "work_order": work_order,
            "product_code": "P001",
            "routings": routings,
            "selected_routing": None,
            "machines": [],
            "employees": [],
        }

        self.dialog.op_combo.set_items = MagicMock()
        self.dialog.machine_combo.clear_items = MagicMock()

        self.dialog.on_work_order_changed("WO001")

        self.assertEqual(
            self.dialog.product_value.text(),
            "P001",
        )
        self.assertEqual(
            self.dialog.status_value.text(),
            "RUNNING",
        )
        self.assertEqual(
            self.dialog.plan_qty_value.text(),
            "120",
        )
        self.assertEqual(
            self.dialog.completed_qty_value.text(),
            "45",
        )
        self.assertEqual(
            self.dialog.remaining_qty_value.text(),
            "75",
        )

        self.lookup_service.build_entry_context.assert_called_once_with(
            "WO001"
        )
        self.dialog.op_combo.set_items.assert_called_once()
        self.dialog.machine_combo.clear_items.assert_called_once_with()

    def test_empty_work_order_clears_context(self) -> None:
        self.dialog.product_value.setText("P001")
        self.dialog.status_value.setText("RUNNING")
        self.dialog.plan_qty_value.setText("100")

        self.dialog.op_combo.clear_items = MagicMock()
        self.dialog.machine_combo.clear_items = MagicMock()

        self.dialog.on_work_order_changed("")

        self.assertEqual(
            self.dialog.product_value.text(),
            "-",
        )
        self.assertEqual(
            self.dialog.status_value.text(),
            "-",
        )
        self.assertEqual(
            self.dialog.plan_qty_value.text(),
            "0",
        )
        self.assertEqual(
            self.dialog.completed_qty_value.text(),
            "0",
        )
        self.assertEqual(
            self.dialog.remaining_qty_value.text(),
            "0",
        )

    # ==========================================================
    # Operation / Machine
    # ==========================================================

    def test_operation_change_loads_machines(self) -> None:
        machines = [
            make_machine(
                machine_code="BL02",
                machine_name="CNC 02",
            )
        ]

        self.dialog.work_order_combo.current_value = MagicMock(
            return_value="WO001"
        )
        self.dialog.machine_combo.set_items = MagicMock()

        self.lookup_service.get_machines_for_operation.return_value = (
            machines
        )

        self.dialog.on_operation_changed("OP10")

        self.lookup_service.get_machines_for_operation.assert_called_once_with(
            "WO001",
            "OP10",
        )
        self.dialog.machine_combo.set_items.assert_called_once()

    def test_operation_change_without_context_clears_machines(
        self,
    ) -> None:
        self.dialog.work_order_combo.current_value = MagicMock(
            return_value=None
        )
        self.dialog.machine_combo.clear_items = MagicMock()

        self.dialog.on_operation_changed("OP10")

        self.dialog.machine_combo.clear_items.assert_called_once_with()
        self.lookup_service.get_machines_for_operation.assert_not_called()

    # ==========================================================
    # get_data validation
    # ==========================================================

    def test_get_data_rejects_invalid_time(self) -> None:
        start = datetime(2026, 7, 20, 8, 0)

        self._configure_required_values()
        self.dialog.start_time.set_value(start)
        self.dialog.finish_time.set_value(start)

        self.dialog.ok_qty.setValue(10)
        self.dialog.ng_qty.setValue(0)

        with self.assertRaisesRegex(
            ValueError,
            "Finish Time must be later",
        ):
            self.dialog.get_data()

    def test_get_data_rejects_zero_quantity(self) -> None:
        start = datetime(2026, 7, 20, 8, 0)

        self._configure_required_values()
        self.dialog.start_time.set_value(start)
        self.dialog.finish_time.set_value(
            start + timedelta(hours=1)
        )

        self.dialog.ok_qty.setValue(0)
        self.dialog.ng_qty.setValue(0)

        with self.assertRaisesRegex(
            ValueError,
            "greater than zero",
        ):
            self.dialog.get_data()

    def test_get_data_returns_complete_payload(self) -> None:
        start = datetime(2026, 7, 20, 8, 0)
        finish = start + timedelta(hours=2)

        self._configure_required_values()

        self.dialog.product_value.setText(" p001 ")
        self.dialog.shift_combo.setCurrentText("NIGHT")

        self.dialog.start_time.set_value(start)
        self.dialog.finish_time.set_value(finish)

        self.dialog.ok_qty.setValue(95)
        self.dialog.ng_qty.setValue(5)
        self.dialog.downtime_min.setValue(12.5)
        self.dialog.downtime_reason.setCurrentText(
            "MAINTENANCE"
        )
        self.dialog.remark.setPlainText(
            " Test production entry "
        )

        result = self.dialog.get_data()

        self.assertEqual(
            result["work_order_no"],
            "WO001",
        )
        self.assertEqual(
            result["product_code"],
            "P001",
        )
        self.assertEqual(
            result["op_no"],
            "OP10",
        )
        self.assertEqual(
            result["machine_code"],
            "BL01",
        )
        self.assertEqual(
            result["employee_code"],
            "E001",
        )
        self.assertEqual(
            result["shift"],
            "NIGHT",
        )
        self.assertEqual(
            result["start_time"],
            start,
        )
        self.assertEqual(
            result["finish_time"],
            finish,
        )
        self.assertEqual(
            result["ok_qty"],
            95,
        )
        self.assertEqual(
            result["ng_qty"],
            5,
        )
        self.assertEqual(
            result["downtime_min"],
            12.5,
        )
        self.assertEqual(
            result["downtime_reason"],
            "MAINTENANCE",
        )
        self.assertEqual(
            result["status"],
            "COMPLETED",
        )
        self.assertEqual(
            result["remark"],
            "Test production entry",
        )

    # ==========================================================
    # Clear
    # ==========================================================

    def test_clear_form_resets_values(self) -> None:
        self.dialog.ok_qty.setValue(100)
        self.dialog.ng_qty.setValue(8)
        self.dialog.downtime_min.setValue(25.5)
        self.dialog.downtime_reason.setCurrentIndex(1)
        self.dialog.remark.setPlainText("Temporary note")

        self.dialog.last_engine_result = object()
        self.dialog.last_execution_result = object()

        self.dialog.kpi_widget.clear_values = MagicMock()
        self.dialog.warning_panel.clear_messages = MagicMock()

        self.dialog.clear_form()

        self.assertEqual(
            self.dialog.ok_qty.value(),
            0,
        )
        self.assertEqual(
            self.dialog.ng_qty.value(),
            0,
        )
        self.assertEqual(
            self.dialog.downtime_min.value(),
            0.0,
        )
        self.assertEqual(
            self.dialog.downtime_reason.currentIndex(),
            0,
        )
        self.assertEqual(
            self.dialog.remark.toPlainText(),
            "",
        )
        self.assertIsNone(
            self.dialog.last_engine_result
        )
        self.assertIsNone(
            self.dialog.last_execution_result
        )

        self.dialog.kpi_widget.clear_values.assert_called_once_with()
        self.dialog.warning_panel.clear_messages.assert_called_once_with()

    # ==========================================================
    # Helpers
    # ==========================================================

    def _configure_required_values(self) -> None:
        self.dialog.work_order_combo.require_value = MagicMock(
            return_value="WO001"
        )
        self.dialog.op_combo.require_value = MagicMock(
            return_value="OP10"
        )
        self.dialog.machine_combo.require_value = MagicMock(
            return_value="BL01"
        )
        self.dialog.employee_combo.require_value = MagicMock(
            return_value="E001"
        )


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)