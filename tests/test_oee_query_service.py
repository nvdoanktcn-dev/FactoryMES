import unittest
from datetime import date, datetime
from types import SimpleNamespace

from src.services.oee_query_service import (
    OEEQueryService,
)


class FakeExecutionRepository:
    def __init__(self, by_assignment=None):
        self.by_assignment = (
            by_assignment or {}
        )

    def get_by_assignment_id(
        self,
        assignment_id,
    ):
        return list(
            self.by_assignment.get(
                assignment_id,
                [],
            )
        )


class FakeAssignmentRepository:
    def __init__(self, assignments=None):
        self.assignments = assignments or []

    def get_by_id(self, assignment_id):
        for item in self.assignments:
            if item.id == int(assignment_id):
                return item
        return None

    def get_by_production_order_id(
        self,
        production_order_id,
    ):
        return [
            item
            for item in self.assignments
            if item.production_order_id
            == int(production_order_id)
        ]

    def get_by_machine(self, machine_code):
        code = str(machine_code).upper()
        return [
            item
            for item in self.assignments
            if item.machine_code.upper()
            == code
        ]

    def get_by_employee(self, employee_code):
        code = str(employee_code).upper()
        return [
            item
            for item in self.assignments
            if item.employee_code.upper()
            == code
        ]

    def get_active_assignments(self):
        return list(self.assignments)

    def get_all(self):
        return list(self.assignments)


class FakeOrderRepository:
    def __init__(self, orders=None):
        self.orders = orders or []

    def get_by_id(self, order_id):
        for item in self.orders:
            if item.id == int(order_id):
                return item
        return None

    def get_by_work_order(
        self,
        work_order_no,
    ):
        number = str(
            work_order_no
        ).upper()
        return [
            item
            for item in self.orders
            if item.work_order_no.upper()
            == number
        ]

    def get_open_orders(self):
        return list(self.orders)

    def get_all(self):
        return list(self.orders)


class FakeRoutingRepository:
    def __init__(self, routings=None):
        self.routings = routings or []

    def get_by_product_operation(
        self,
        product_code,
        operation_no,
    ):
        code = str(product_code).upper()
        operation = int(operation_no)

        for item in self.routings:
            if (
                item.product_code.upper()
                == code
                and int(item.operation_no)
                == operation
            ):
                return item

        return None


class TestOEEQueryService(unittest.TestCase):
    def setUp(self):
        self.order_1 = SimpleNamespace(
            id=1,
            work_order_no="WO-001",
            product_code="P-001",
            operation_no=1,
        )
        self.order_2 = SimpleNamespace(
            id=2,
            work_order_no="WO-002",
            product_code="P-002",
            operation_no=2,
        )

        self.assignment_1 = SimpleNamespace(
            id=11,
            production_order_id=1,
            machine_code="BL-01",
            employee_code="NV-01",
            shift="DAY",
        )
        self.assignment_2 = SimpleNamespace(
            id=12,
            production_order_id=2,
            machine_code="BL-02",
            employee_code="NV-02",
            shift="NIGHT",
        )

        self.execution_1 = SimpleNamespace(
            id=101,
            start_time=datetime(
                2026, 7, 1, 8, 0
            ),
            end_time=datetime(
                2026, 7, 1, 16, 0
            ),
            runtime_minutes=420,
            downtime_minutes=60,
            ok_qty=995,
            ng_qty=5,
            status="COMPLETED",
        )
        self.execution_2 = SimpleNamespace(
            id=102,
            start_time=datetime(
                2026, 7, 2, 20, 0
            ),
            end_time=datetime(
                2026, 7, 3, 4, 0
            ),
            runtime_minutes=400,
            downtime_minutes=80,
            ok_qty=790,
            ng_qty=10,
            status="COMPLETED",
        )

        self.routing_1 = SimpleNamespace(
            product_code="P-001",
            operation_no=1,
            cycle_time_sec=20,
        )
        self.routing_2 = SimpleNamespace(
            product_code="P-002",
            operation_no=2,
            cycle_time_sec=30,
        )

        self.service = OEEQueryService(
            execution_repository=(
                FakeExecutionRepository(
                    {
                        11: [self.execution_1],
                        12: [self.execution_2],
                    }
                )
            ),
            assignment_repository=(
                FakeAssignmentRepository(
                    [
                        self.assignment_1,
                        self.assignment_2,
                    ]
                )
            ),
            production_order_repository=(
                FakeOrderRepository(
                    [
                        self.order_1,
                        self.order_2,
                    ]
                )
            ),
            routing_repository=(
                FakeRoutingRepository(
                    [
                        self.routing_1,
                        self.routing_2,
                    ]
                )
            ),
        )

    def test_get_assignment_oee(self):
        result = (
            self.service
            .get_assignment_oee(11)
        )

        self.assertEqual(
            result.total_qty,
            1000,
        )
        self.assertAlmostEqual(
            result.availability,
            0.875,
            places=6,
        )

    def test_assignment_not_found_returns_empty(self):
        result = (
            self.service
            .get_assignment_oee(999)
        )

        self.assertEqual(result.oee, 0.0)
        self.assertEqual(result.total_qty, 0)

    def test_get_machine_oee(self):
        result = (
            self.service
            .get_machine_oee(" bl-01 ")
        )

        self.assertEqual(result.ok_qty, 995)
        self.assertEqual(result.ng_qty, 5)

    def test_get_employee_oee(self):
        result = (
            self.service
            .get_employee_oee("nv-02")
        )

        self.assertEqual(result.ok_qty, 790)
        self.assertEqual(result.ng_qty, 10)

    def test_get_shift_oee(self):
        result = (
            self.service
            .get_shift_oee("night")
        )

        self.assertEqual(result.total_qty, 800)

    def test_get_product_oee(self):
        result = (
            self.service
            .get_product_oee("p-001")
        )

        self.assertEqual(result.total_qty, 1000)

    def test_get_work_order_oee(self):
        result = (
            self.service
            .get_work_order_oee("wo-002")
        )

        self.assertEqual(result.total_qty, 800)

    def test_get_all_oee(self):
        result = self.service.get_all_oee()

        self.assertEqual(result.total_qty, 1800)
        self.assertEqual(result.ok_qty, 1785)
        self.assertEqual(result.ng_qty, 15)

    def test_daily_oee(self):
        result = (
            self.service
            .get_daily_oee(
                date(2026, 7, 1)
            )
        )

        self.assertEqual(result.total_qty, 1000)

    def test_daily_oee_accepts_iso_string(self):
        result = (
            self.service
            .get_daily_oee("2026-07-02")
        )

        self.assertEqual(result.total_qty, 800)

    def test_monthly_oee(self):
        result = (
            self.service
            .get_monthly_oee(2026, 7)
        )

        self.assertEqual(result.total_qty, 1800)

    def test_date_range_filters_execution(self):
        result = self.service.get_all_oee(
            start_time=datetime(
                2026, 7, 2
            ),
            end_time=datetime(
                2026, 7, 4
            ),
        )

        self.assertEqual(result.total_qty, 800)

    def test_overlapping_execution_is_included(self):
        result = self.service.get_all_oee(
            start_time=datetime(
                2026, 7, 1, 12
            ),
            end_time=datetime(
                2026, 7, 1, 13
            ),
        )

        self.assertEqual(result.total_qty, 1000)

    def test_running_execution_is_ignored(self):
        self.execution_1.status = "RUNNING"

        result = (
            self.service
            .get_machine_oee("BL-01")
        )

        self.assertEqual(result.total_qty, 0)

    def test_cancelled_execution_is_ignored(self):
        self.execution_1.status = "CANCELLED"

        result = (
            self.service
            .get_machine_oee("BL-01")
        )

        self.assertEqual(result.total_qty, 0)

    def test_only_final_operation_contributes_output(self):
        order_op_2 = SimpleNamespace(
            id=3,
            work_order_no="WO-001",
            product_code="P-001",
            operation_no=2,
        )
        assignment_op_2 = SimpleNamespace(
            id=13,
            production_order_id=3,
            machine_code="BL-03",
            employee_code="NV-03",
            shift="DAY",
        )
        execution_op_2 = SimpleNamespace(
            id=103,
            start_time=datetime(2026, 7, 1, 8, 0),
            end_time=datetime(2026, 7, 1, 16, 0),
            runtime_minutes=400,
            downtime_minutes=80,
            ok_qty=790,
            ng_qty=10,
            status="COMPLETED",
        )
        routing_op_2 = SimpleNamespace(
            product_code="P-001",
            operation_no=2,
            cycle_time_sec=30,
        )
        service = OEEQueryService(
            execution_repository=FakeExecutionRepository(
                {
                    11: [self.execution_1],
                    13: [execution_op_2],
                }
            ),
            assignment_repository=FakeAssignmentRepository(
                [self.assignment_1, assignment_op_2]
            ),
            production_order_repository=FakeOrderRepository(
                [self.order_1, order_op_2]
            ),
            routing_repository=FakeRoutingRepository(
                [self.routing_1, routing_op_2]
            ),
        )

        result = service.get_work_order_oee("WO-001")

        self.assertEqual(result.runtime_minutes, 820)
        self.assertEqual(result.downtime_minutes, 140)
        self.assertEqual(result.total_qty, 800)
        self.assertEqual(result.ok_qty, 790)
        self.assertEqual(result.ng_qty, 10)

    def test_non_final_machine_keeps_time_without_output(self):
        order_op_2 = SimpleNamespace(
            id=3,
            work_order_no="WO-001",
            product_code="P-001",
            operation_no=2,
        )
        service = OEEQueryService(
            execution_repository=FakeExecutionRepository(
                {11: [self.execution_1]}
            ),
            assignment_repository=FakeAssignmentRepository(
                [self.assignment_1]
            ),
            production_order_repository=FakeOrderRepository(
                [self.order_1, order_op_2]
            ),
            routing_repository=FakeRoutingRepository(
                [self.routing_1]
            ),
        )

        result = service.get_machine_oee("BL-01")

        self.assertEqual(result.runtime_minutes, 420)
        self.assertEqual(result.downtime_minutes, 60)
        self.assertEqual(result.total_qty, 0)

    def test_execution_without_start_is_ignored(self):
        self.execution_1.start_time = None

        result = (
            self.service
            .get_machine_oee("BL-01")
        )

        self.assertEqual(result.total_qty, 0)

    def test_missing_order_is_ignored(self):
        self.assignment_1.production_order_id = 999

        result = (
            self.service
            .get_machine_oee("BL-01")
        )

        self.assertEqual(result.total_qty, 0)

    def test_missing_routing_fails(self):
        service = OEEQueryService(
            execution_repository=(
                FakeExecutionRepository(
                    {11: [self.execution_1]}
                )
            ),
            assignment_repository=(
                FakeAssignmentRepository(
                    [self.assignment_1]
                )
            ),
            production_order_repository=(
                FakeOrderRepository(
                    [self.order_1]
                )
            ),
            routing_repository=(
                FakeRoutingRepository([])
            ),
        )

        with self.assertRaisesRegex(
            ValueError,
            "Routing not found",
        ):
            service.get_machine_oee("BL-01")

    def test_empty_machine_code_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Machine Code is required",
        ):
            self.service.get_machine_oee("")

    def test_empty_employee_code_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Employee Code is required",
        ):
            self.service.get_employee_oee(None)

    def test_empty_shift_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Shift is required",
        ):
            self.service.get_shift_oee("")

    def test_empty_product_code_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Product Code is required",
        ):
            self.service.get_product_oee(" ")

    def test_empty_work_order_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Work Order No is required",
        ):
            self.service.get_work_order_oee(None)

    def test_invalid_range_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "End Time must be after Start Time",
        ):
            self.service.get_all_oee(
                start_time=datetime(
                    2026, 7, 2
                ),
                end_time=datetime(
                    2026, 7, 1
                ),
            )

    def test_equal_range_fails(self):
        moment = datetime(2026, 7, 1)

        with self.assertRaisesRegex(
            ValueError,
            "End Time must be after Start Time",
        ):
            self.service.get_all_oee(
                start_time=moment,
                end_time=moment,
            )

    def test_iso_datetime_range(self):
        result = self.service.get_all_oee(
            start_time="2026-07-01T00:00:00",
            end_time="2026-07-02T00:00:00",
        )

        self.assertEqual(result.total_qty, 1000)

    def test_invalid_datetime_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Invalid Start Time",
        ):
            self.service.get_all_oee(
                start_time="invalid",
            )

    def test_invalid_daily_date_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Invalid Target Date",
        ):
            self.service.get_daily_oee(
                "2026-99-99"
            )

    def test_invalid_month_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Invalid year or month",
        ):
            self.service.get_monthly_oee(
                2026,
                13,
            )


if __name__ == "__main__":
    unittest.main()
