from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.framework.exception import (
    NotFoundError,
    ValidationError,
)
from src.services.production_entry_lookup_service import (
    ProductionEntryLookupService,
)


def make_work_order(
    *,
    work_order_no="WO001",
    product_code="P001",
    status="PLANNED",
):
    return SimpleNamespace(
        work_order_no=work_order_no,
        product_code=product_code,
        status=status,
    )


def make_routing(
    *,
    op_no="OP10",
    sequence=1,
    status="ACTIVE",
    machine_code="",
    machine_type="CNC",
):
    return SimpleNamespace(
        op_no=op_no,
        sequence=sequence,
        status=status,
        machine_code=machine_code,
        machine_type=machine_type,
    )


def make_machine(
    *,
    machine_code="BL01",
    machine_type="CNC",
    status="ACTIVE",
):
    return SimpleNamespace(
        machine_code=machine_code,
        machine_type=machine_type,
        status=status,
    )


def make_employee(
    *,
    employee_code="E001",
    status="ACTIVE",
):
    return SimpleNamespace(
        employee_code=employee_code,
        status=status,
    )


class TestProductionEntryLookupService(unittest.TestCase):

    def setUp(self) -> None:
        self.session = MagicMock()

        self.service = ProductionEntryLookupService(
            session=self.session
        )

        self.service.work_order_repository = MagicMock()
        self.service.routing_repository = MagicMock()
        self.service.machine_repository = MagicMock()
        self.service.employee_repository = MagicMock()

    # ==========================================================
    # Normalization
    # ==========================================================

    def test_normalize_code(self) -> None:
        self.assertEqual(
            self.service._normalize_code(" wo001 "),
            "WO001",
        )
        self.assertEqual(
            self.service._normalize_code(None),
            "",
        )

    def test_normalize_op_from_digits(self) -> None:
        self.assertEqual(
            self.service._normalize_op("10"),
            "OP10",
        )
        self.assertEqual(
            self.service._normalize_op("op010"),
            "OP10",
        )

    def test_normalize_op_without_digits(self) -> None:
        self.assertEqual(
            self.service._normalize_op("finish"),
            "FINISH",
        )

    # ==========================================================
    # Work Order
    # ==========================================================

    def test_get_available_work_orders_filters_and_sorts(
        self,
    ) -> None:
        self.service.work_order_repository.get_all.return_value = [
            make_work_order(
                work_order_no="WO003",
                status="CLOSED",
            ),
            make_work_order(
                work_order_no="WO002",
                status="RUNNING",
            ),
            make_work_order(
                work_order_no="WO001",
                status=" planned ",
            ),
        ]

        result = self.service.get_available_work_orders()

        self.assertEqual(
            [item.work_order_no for item in result],
            ["WO001", "WO002"],
        )

    def test_get_work_order_requires_number(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.get_work_order("   ")

    def test_get_work_order_not_found(self) -> None:
        self.service.work_order_repository.get_by_no.return_value = (
            None
        )

        with self.assertRaises(NotFoundError):
            self.service.get_work_order("WO404")

        self.service.work_order_repository.get_by_no.assert_called_once_with(
            "WO404"
        )

    def test_get_work_order_returns_record(self) -> None:
        work_order = make_work_order()

        self.service.work_order_repository.get_by_no.return_value = (
            work_order
        )

        result = self.service.get_work_order(" wo001 ")

        self.assertIs(result, work_order)

    # ==========================================================
    # Routing
    # ==========================================================

    def test_get_work_order_routing_filters_and_sorts(
        self,
    ) -> None:
        work_order = make_work_order(
            product_code=" p001 "
        )

        self.service.work_order_repository.get_by_no.return_value = (
            work_order
        )

        self.service.routing_repository.get_by_product.return_value = [
            make_routing(
                op_no="OP20",
                sequence=2,
            ),
            make_routing(
                op_no="OP30",
                sequence=3,
                status="INACTIVE",
            ),
            make_routing(
                op_no="OP10",
                sequence=1,
            ),
        ]

        result = self.service.get_work_order_routing(
            "WO001"
        )

        self.assertEqual(
            [item.op_no for item in result],
            ["OP10", "OP20"],
        )

        self.service.routing_repository.get_by_product.assert_called_once_with(
            "P001"
        )

    def test_get_work_order_routing_requires_active_routing(
        self,
    ) -> None:
        self.service.work_order_repository.get_by_no.return_value = (
            make_work_order()
        )

        self.service.routing_repository.get_by_product.return_value = [
            make_routing(status="INACTIVE")
        ]

        with self.assertRaises(NotFoundError):
            self.service.get_work_order_routing(
                "WO001"
            )

    def test_get_routing_operation_normalizes_op(
        self,
    ) -> None:
        routing = make_routing(op_no="OP10")

        self.service.get_work_order_routing = MagicMock(
            return_value=[routing]
        )

        result = self.service.get_routing_operation(
            "WO001",
            "10",
        )

        self.assertIs(result, routing)

    def test_get_routing_operation_not_found(
        self,
    ) -> None:
        self.service.get_work_order_routing = MagicMock(
            return_value=[
                make_routing(op_no="OP10")
            ]
        )

        with self.assertRaises(NotFoundError):
            self.service.get_routing_operation(
                "WO001",
                "OP20",
            )

    # ==========================================================
    # Machine
    # ==========================================================

    def test_get_machines_matches_specific_machine_code(
        self,
    ) -> None:
        routing = make_routing(
            machine_code="BL02",
            machine_type="CNC",
        )

        self.service.get_routing_operation = MagicMock(
            return_value=routing
        )

        self.service.machine_repository.get_all.return_value = [
            make_machine(
                machine_code="BL01",
                status="ACTIVE",
            ),
            make_machine(
                machine_code="BL02",
                status="READY",
            ),
            make_machine(
                machine_code="BL03",
                status="STOPPED",
            ),
        ]

        result = self.service.get_machines_for_operation(
            "WO001",
            "OP10",
        )

        self.assertEqual(
            [item.machine_code for item in result],
            ["BL02"],
        )

    def test_get_machines_matches_machine_type(
        self,
    ) -> None:
        routing = make_routing(
            machine_code="",
            machine_type="CNC",
        )

        self.service.get_routing_operation = MagicMock(
            return_value=routing
        )

        self.service.machine_repository.get_all.return_value = [
            make_machine(
                machine_code="BL02",
                machine_type="CNC",
                status="READY",
            ),
            make_machine(
                machine_code="BL01",
                machine_type="CNC",
                status="ACTIVE",
            ),
            make_machine(
                machine_code="BR01",
                machine_type="ROBOT",
                status="ACTIVE",
            ),
        ]

        result = self.service.get_machines_for_operation(
            "WO001",
            "OP10",
        )

        self.assertEqual(
            [item.machine_code for item in result],
            ["BL01", "BL02"],
        )

    def test_get_machines_excludes_inactive_machine(
        self,
    ) -> None:
        routing = make_routing(
            machine_code="",
            machine_type="CNC",
        )

        self.service.get_routing_operation = MagicMock(
            return_value=routing
        )

        self.service.machine_repository.get_all.return_value = [
            make_machine(
                machine_code="BL01",
                machine_type="CNC",
                status="STOPPED",
            )
        ]

        result = self.service.get_machines_for_operation(
            "WO001",
            "OP10",
        )

        self.assertEqual(result, [])

    # ==========================================================
    # Employee
    # ==========================================================

    def test_get_active_employees_filters_and_sorts(
        self,
    ) -> None:
        self.service.employee_repository.get_all.return_value = [
            make_employee(
                employee_code="E003",
                status="INACTIVE",
            ),
            make_employee(
                employee_code="E002",
                status="ACTIVE",
            ),
            make_employee(
                employee_code="E001",
                status=" active ",
            ),
        ]

        result = self.service.get_active_employees()

        self.assertEqual(
            [item.employee_code for item in result],
            ["E001", "E002"],
        )

    # ==========================================================
    # Context
    # ==========================================================

    def test_build_entry_context_without_operation(
        self,
    ) -> None:
        work_order = make_work_order()
        routings = [
            make_routing(op_no="OP10")
        ]
        employees = [
            make_employee()
        ]

        self.service.get_work_order = MagicMock(
            return_value=work_order
        )
        self.service.get_work_order_routing = MagicMock(
            return_value=routings
        )
        self.service.get_active_employees = MagicMock(
            return_value=employees
        )

        context = self.service.build_entry_context(
            "WO001"
        )

        self.assertIs(
            context["work_order"],
            work_order,
        )
        self.assertEqual(
            context["product_code"],
            "P001",
        )
        self.assertEqual(
            context["routings"],
            routings,
        )
        self.assertIsNone(
            context["selected_routing"]
        )
        self.assertEqual(
            context["machines"],
            [],
        )
        self.assertEqual(
            context["employees"],
            employees,
        )

    def test_build_entry_context_with_operation(
        self,
    ) -> None:
        work_order = make_work_order()
        routings = [
            make_routing(op_no="OP10")
        ]
        selected_routing = routings[0]
        machines = [
            make_machine()
        ]
        employees = [
            make_employee()
        ]

        self.service.get_work_order = MagicMock(
            return_value=work_order
        )
        self.service.get_work_order_routing = MagicMock(
            return_value=routings
        )
        self.service.get_routing_operation = MagicMock(
            return_value=selected_routing
        )
        self.service.get_machines_for_operation = MagicMock(
            return_value=machines
        )
        self.service.get_active_employees = MagicMock(
            return_value=employees
        )

        context = self.service.build_entry_context(
            "WO001",
            "OP10",
        )

        self.assertIs(
            context["selected_routing"],
            selected_routing,
        )
        self.assertEqual(
            context["machines"],
            machines,
        )

        self.service.get_routing_operation.assert_called_once_with(
            "WO001",
            "OP10",
        )

        self.service.get_machines_for_operation.assert_called_once_with(
            "WO001",
            "OP10",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)