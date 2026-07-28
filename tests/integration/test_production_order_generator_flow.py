from __future__ import annotations

from datetime import date, datetime, timedelta

from tests.base.database_test_case import DatabaseTestCase

from src.services.product_service import ProductService
from src.services.production_order_generator import (
    ProductionOrderGenerator,
)
from src.services.production_order_service import (
    ProductionOrderService,
)
from src.services.routing_service import RoutingService
from src.services.work_order_service import WorkOrderService


class TestProductionOrderGeneratorFlow(DatabaseTestCase):
    """Integration tests for Work Order -> Production Order generation."""

    def setUp(self):
        super().setUp()

        self.product_service = ProductService(
            session=self.session,
        )
        self.routing_service = RoutingService(
            session=self.session,
        )
        self.work_order_service = WorkOrderService(
            session=self.session,
        )
        self.production_order_service = ProductionOrderService(
            session=self.session,
        )
        self.generator = ProductionOrderGenerator(
            session=self.session,
        )

    def _create_product(self, product_code):
        return self.product_service.create_product(
            product_code=product_code,
            product_name_vi=f"Integration Product {product_code}",
            customer="INTEGRATION CUSTOMER",
            material="STEEL",
            unit="PCS",
            status="ACTIVE",
        )

    def _create_routing(
        self,
        *,
        product_code,
        operation_no,
        operation_name,
        process_type,
        machine_type,
        cycle_time_sec,
        status="ACTIVE",
        remark=None,
    ):
        return self.routing_service.create_routing(
            {
                "product_code": product_code,
                "operation_no": operation_no,
                "operation_name": operation_name,
                "process_type": process_type,
                "machine_type": machine_type,
                "standard_cycle_time_sec": cycle_time_sec,
                "standard_output_pcs_hour": (
                    3600.0 / cycle_time_sec
                ),
                "standard_operator_count": 1,
                "status": status,
                "remark": remark,
            }
        )

    def _create_work_order(
        self,
        *,
        work_order_no,
        product_code,
        plan_qty=100,
        release=True,
    ):
        work_order = self.work_order_service.create_work_order(
            {
                "work_order_no": work_order_no,
                "product_code": product_code,
                "plan_qty": plan_qty,
                "start_date": date(2026, 7, 28),
                "due_date": date(2026, 8, 28),
                "priority": "NORMAL",
                "status": "PLANNED",
                "remark": "Production generator integration test",
            }
        )

        if release:
            work_order = (
                self.work_order_service.release_work_order(
                    work_order_no
                )
            )

        self.session.flush()
        return work_order

    def test_generate_orders_from_active_routing(self):
        product_code = "INT-GEN-001"
        work_order_no = "WO-INT-GEN-001"

        self._create_product(product_code)

        self._create_routing(
            product_code=product_code,
            operation_no=10,
            operation_name="CNC Roughing",
            process_type="CNC",
            machine_type="CNC",
            cycle_time_sec=36,
            remark="First operation",
        )
        self._create_routing(
            product_code=product_code,
            operation_no=20,
            operation_name="Robot Welding",
            process_type="ROBOT",
            machine_type="ROBOT",
            cycle_time_sec=72,
        )
        self._create_routing(
            product_code=product_code,
            operation_no=30,
            operation_name="Final Inspection",
            process_type="INSPECTION",
            machine_type="INSPECTION",
            cycle_time_sec=18,
            remark="Quality gate",
        )

        work_order = self._create_work_order(
            work_order_no=work_order_no,
            product_code=product_code,
            plan_qty=100,
        )

        result = self.generator.generate(
            work_order_no,
            auto_commit=False,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["work_order_no"], work_order_no)
        self.assertEqual(result["product_code"], product_code)
        self.assertEqual(result["routing_count"], 3)
        self.assertEqual(result["created_count"], 3)
        self.assertEqual(result["skipped_count"], 0)
        self.assertEqual(result["last_operation_no"], 30)

        generated = (
            self.production_order_service.get_by_work_order(
                work_order_no
            )
        )

        self.assertEqual(len(generated), 3)

        generated.sort(
            key=lambda order: int(order.operation_no)
        )

        first, second, third = generated

        self.assertEqual(
            [order.operation_no for order in generated],
            [10, 20, 30],
        )

        for order in generated:
            self.assertEqual(
                order.work_order_no,
                work_order.work_order_no,
            )
            self.assertEqual(
                order.product_code,
                product_code,
            )
            self.assertEqual(order.plan_qty, 100)
            self.assertEqual(order.completed_qty, 0)
            self.assertEqual(order.ng_qty, 0)
            self.assertEqual(order.status, "PLANNED")
            self.assertIsNone(order.machine_code)
            self.assertIsNone(order.employee_code)
            self.assertIsNone(order.shift)
            self.assertIsNone(order.actual_start)
            self.assertIsNone(order.actual_finish)

        expected_start = datetime(2026, 7, 28, 8, 0)

        self.assertEqual(
            first.planned_start,
            expected_start,
        )
        self.assertEqual(
            first.planned_finish,
            expected_start + timedelta(hours=1),
        )

        self.assertEqual(
            second.planned_start,
            first.planned_finish,
        )
        self.assertEqual(
            second.planned_finish,
            second.planned_start + timedelta(hours=2),
        )

        self.assertEqual(
            third.planned_start,
            second.planned_finish,
        )
        self.assertEqual(
            third.planned_finish,
            third.planned_start
            + timedelta(hours=0.5),
        )

        self.assertIn(
            "First operation",
            first.remark or "",
        )
        self.assertNotIn(
            "FINAL_OPERATION",
            first.remark or "",
        )
        self.assertNotIn(
            "FINAL_OPERATION",
            second.remark or "",
        )
        self.assertIn(
            "FINAL_OPERATION",
            third.remark or "",
        )
        self.assertIn(
            "Quality gate",
            third.remark or "",
        )

    def test_generate_twice_skips_existing_operations(self):
        product_code = "INT-GEN-002"
        work_order_no = "WO-INT-GEN-002"

        self._create_product(product_code)

        self._create_routing(
            product_code=product_code,
            operation_no=10,
            operation_name="Machining",
            process_type="CNC",
            machine_type="CNC",
            cycle_time_sec=30,
        )
        self._create_routing(
            product_code=product_code,
            operation_no=20,
            operation_name="Inspection",
            process_type="INSPECTION",
            machine_type="INSPECTION",
            cycle_time_sec=15,
        )

        self._create_work_order(
            work_order_no=work_order_no,
            product_code=product_code,
            plan_qty=120,
        )

        first_result = self.generator.generate(
            work_order_no,
            auto_commit=False,
        )
        second_result = self.generator.generate(
            work_order_no,
            auto_commit=False,
        )

        self.assertEqual(first_result["created_count"], 2)
        self.assertEqual(first_result["skipped_count"], 0)

        self.assertEqual(second_result["created_count"], 0)
        self.assertEqual(second_result["skipped_count"], 2)

        generated = (
            self.production_order_service.get_by_work_order(
                work_order_no
            )
        )

        self.assertEqual(len(generated), 2)
        self.assertEqual(
            sorted(
                order.operation_no
                for order in generated
            ),
            [10, 20],
        )

    def test_generate_uses_only_active_routings(self):
        product_code = "INT-GEN-003"
        work_order_no = "WO-INT-GEN-003"

        self._create_product(product_code)

        self._create_routing(
            product_code=product_code,
            operation_no=10,
            operation_name="Active Machining",
            process_type="CNC",
            machine_type="CNC",
            cycle_time_sec=30,
            status="ACTIVE",
        )
        self._create_routing(
            product_code=product_code,
            operation_no=20,
            operation_name="Inactive Washing",
            process_type="MANUAL",
            machine_type="MANUAL",
            cycle_time_sec=20,
            status="INACTIVE",
        )
        self._create_routing(
            product_code=product_code,
            operation_no=30,
            operation_name="Active Inspection",
            process_type="INSPECTION",
            machine_type="INSPECTION",
            cycle_time_sec=15,
            status="ACTIVE",
        )

        self._create_work_order(
            work_order_no=work_order_no,
            product_code=product_code,
            plan_qty=60,
        )

        result = self.generator.generate(
            work_order_no,
            auto_commit=False,
        )

        self.assertEqual(result["routing_count"], 2)
        self.assertEqual(result["created_count"], 2)
        self.assertEqual(result["last_operation_no"], 30)

        generated = (
            self.production_order_service.get_by_work_order(
                work_order_no
            )
        )
        generated.sort(
            key=lambda order: int(order.operation_no)
        )

        self.assertEqual(
            [order.operation_no for order in generated],
            [10, 30],
        )
        self.assertNotIn(
            "FINAL_OPERATION",
            generated[0].remark or "",
        )
        self.assertIn(
            "FINAL_OPERATION",
            generated[1].remark or "",
        )

    def test_cancelled_work_order_cannot_generate_orders(self):
        product_code = "INT-GEN-004"
        work_order_no = "WO-INT-GEN-004"

        self._create_product(product_code)

        self._create_routing(
            product_code=product_code,
            operation_no=10,
            operation_name="Machining",
            process_type="CNC",
            machine_type="CNC",
            cycle_time_sec=30,
        )

        self._create_work_order(
            work_order_no=work_order_no,
            product_code=product_code,
            plan_qty=100,
            release=False,
        )

        self.work_order_service.delete_work_order(
            work_order_no
        )
        self.session.flush()

        with self.assertRaisesRegex(
            ValueError,
            "CANCELLED Work Order",
        ):
            self.generator.generate(
                work_order_no,
                auto_commit=False,
            )

        generated = (
            self.production_order_service.get_by_work_order(
                work_order_no
            )
        )
        self.assertEqual(generated, [])

    def test_product_without_active_routing_cannot_generate(self):
        product_code = "INT-GEN-005"
        work_order_no = "WO-INT-GEN-005"

        self._create_product(product_code)

        self._create_routing(
            product_code=product_code,
            operation_no=10,
            operation_name="Inactive Operation",
            process_type="MANUAL",
            machine_type="MANUAL",
            cycle_time_sec=30,
            status="INACTIVE",
        )

        self._create_work_order(
            work_order_no=work_order_no,
            product_code=product_code,
            plan_qty=100,
        )

        with self.assertRaisesRegex(
            ValueError,
            "No ACTIVE Routing found",
        ):
            self.generator.generate(
                work_order_no,
                auto_commit=False,
            )

        generated = (
            self.production_order_service.get_by_work_order(
                work_order_no
            )
        )
        self.assertEqual(generated, [])
