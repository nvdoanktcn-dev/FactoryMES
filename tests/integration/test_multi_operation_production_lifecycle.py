from __future__ import annotations

from datetime import date, datetime

from tests.base.database_test_case import DatabaseTestCase
from tests.factories.employee_factory import EmployeeFactory
from tests.factories.machine_factory import MachineFactory
from tests.factories.production_assignment_factory import (
    ProductionAssignmentFactory,
)

from src.services.product_service import ProductService
from src.services.production_assignment_service import (
    ProductionAssignmentService,
)
from src.services.production_execution_service import (
    ProductionExecutionService,
)
from src.services.production_order_generator import (
    ProductionOrderGenerator,
)
from src.services.production_order_service import (
    ProductionOrderService,
)
from src.services.routing_service import RoutingService
from src.services.work_order_service import WorkOrderService


class TestMultiOperationProductionLifecycle(DatabaseTestCase):
    """
    Verify a complete multi-operation production lifecycle.

    Product
        -> Routing OP10 / OP20 / OP30
        -> Work Order
        -> generated Production Orders
        -> Assignment per operation
        -> Execution per operation
        -> completed Work Order
    """

    PRODUCT_CODE = "INT-MULTI-001"
    WORK_ORDER_NO = "WO-INT-MULTI-001"
    PLAN_QTY = 100

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
        self.assignment_service = ProductionAssignmentService(
            session=self.session,
        )
        self.execution_service = ProductionExecutionService(
            session=self.session,
        )
        self.generator = ProductionOrderGenerator(
            session=self.session,
        )

    def _create_product(self):
        return self.product_service.create_product(
            product_code=self.PRODUCT_CODE,
            product_name_vi="Multi-operation Integration Product",
            customer="INTEGRATION CUSTOMER",
            material="STEEL",
            unit="PCS",
            status="ACTIVE",
        )

    def _create_routing(
        self,
        *,
        operation_no,
        operation_name,
        process_type,
        machine_type,
        cycle_time_sec,
        remark=None,
    ):
        return self.routing_service.create_routing(
            {
                "product_code": self.PRODUCT_CODE,
                "operation_no": operation_no,
                "operation_name": operation_name,
                "process_type": process_type,
                "machine_type": machine_type,
                "standard_cycle_time_sec": cycle_time_sec,
                "standard_output_pcs_hour": (
                    3600.0 / cycle_time_sec
                ),
                "standard_operator_count": 1,
                "status": "ACTIVE",
                "remark": remark,
            }
        )

    def _create_work_order(self):
        work_order = self.work_order_service.create_work_order(
            {
                "work_order_no": self.WORK_ORDER_NO,
                "product_code": self.PRODUCT_CODE,
                "plan_qty": self.PLAN_QTY,
                "start_date": date(2026, 7, 28),
                "due_date": date(2026, 8, 28),
                "priority": "NORMAL",
                "status": "PLANNED",
                "remark": (
                    "Multi-operation production lifecycle "
                    "integration test"
                ),
            }
        )

        work_order = self.work_order_service.release_work_order(
            self.WORK_ORDER_NO
        )

        self.session.flush()

        return work_order

    def _complete_operation(
        self,
        *,
        production_order,
        machine,
        employee,
        actual_start,
        actual_finish,
        ok_qty,
        ng_qty,
        processing_ng_qty,
        blank_ng_qty,
        downtime_minutes,
    ):
        # ------------------------------------------------------
        # Release the generated Production Order
        # ------------------------------------------------------
        production_order = self.production_order_service.release(
            production_order.work_order_no,
            production_order.operation_no,
        )

        self.session.flush()

        self.assertEqual(
            production_order.status,
            "RELEASED",
        )

        # ------------------------------------------------------
        # Create and release a dedicated Assignment
        # ------------------------------------------------------
        assignment = ProductionAssignmentFactory.create_draft(
            self.session,
            production_order=production_order,
            machine_code=machine.machine_code,
            employee_code=employee.employee_code,
            shift="DAY",
            planned_start=production_order.planned_start,
            planned_finish=production_order.planned_finish,
            remark=(
                "Multi-operation assignment "
                f"OP{production_order.operation_no}"
            ),
        )

        assignment = self.assignment_service.release(
            assignment.id
        )

        self.session.flush()

        self.assertEqual(
            assignment.status,
            "RELEASED",
        )
        self.assertEqual(
            assignment.production_order_id,
            production_order.id,
        )
        self.assertEqual(
            assignment.machine_code,
            machine.machine_code,
        )
        self.assertEqual(
            assignment.employee_code,
            employee.employee_code,
        )

        # ------------------------------------------------------
        # Start Production Order and Assignment
        # ------------------------------------------------------
        production_order = self.production_order_service.start(
            production_order.work_order_no,
            production_order.operation_no,
            actual_start=actual_start,
        )

        assignment = self.assignment_service.start(
            assignment.id,
            actual_start=actual_start,
        )

        self.session.flush()

        self.assertEqual(
            production_order.status,
            "IN_PROGRESS",
        )
        self.assertEqual(
            assignment.status,
            "IN_PROGRESS",
        )

        # ------------------------------------------------------
        # Start and stop a dedicated Execution
        # ------------------------------------------------------
        execution = self.execution_service.start_execution(
            assignment.id,
            start_time=actual_start,
            remark=(
                "Multi-operation execution "
                f"OP{production_order.operation_no}"
            ),
        )

        self.session.flush()

        self.assertIsNotNone(execution.id)
        self.assertEqual(
            execution.assignment_id,
            assignment.id,
        )
        self.assertEqual(
            execution.status,
            "RUNNING",
        )

        execution = self.execution_service.stop_execution(
            execution.id,
            ok_qty=ok_qty,
            ng_qty=ng_qty,
            processing_ng_qty=processing_ng_qty,
            blank_ng_qty=blank_ng_qty,
            downtime_minutes=downtime_minutes,
            end_time=actual_finish,
            complete=True,
        )

        self.session.flush()

        self.assertEqual(
            execution.status,
            "COMPLETED",
        )
        self.assertEqual(
            execution.ok_qty,
            ok_qty,
        )
        self.assertEqual(
            execution.ng_qty,
            ng_qty,
        )
        self.assertEqual(
            execution.processing_ng_qty,
            processing_ng_qty,
        )
        self.assertEqual(
            execution.blank_ng_qty,
            blank_ng_qty,
        )
        self.assertEqual(
            execution.downtime_minutes,
            downtime_minutes,
        )

        # ------------------------------------------------------
        # Complete Assignment and Production Order
        # ------------------------------------------------------
        assignment = self.assignment_service.complete(
            assignment.id,
            actual_finish=actual_finish,
        )

        production_order = self.production_order_service.complete(
            production_order.work_order_no,
            production_order.operation_no,
            completed_qty=ok_qty,
            ng_qty=ng_qty,
            actual_finish=actual_finish,
        )

        self.session.flush()

        self.assertEqual(
            assignment.status,
            "COMPLETED",
        )
        self.assertEqual(
            production_order.status,
            "COMPLETED",
        )
        self.assertEqual(
            production_order.completed_qty,
            execution.ok_qty,
        )
        self.assertEqual(
            production_order.ng_qty,
            execution.ng_qty,
        )

        return {
            "production_order": production_order,
            "assignment": assignment,
            "execution": execution,
        }

    def test_complete_multi_operation_production_lifecycle(self):
        # ------------------------------------------------------
        # Arrange: Product and three ACTIVE Routing operations
        # ------------------------------------------------------
        self._create_product()

        self._create_routing(
            operation_no=10,
            operation_name="CNC Roughing",
            process_type="CNC",
            machine_type="CNC",
            cycle_time_sec=36,
            remark="First operation",
        )
        self._create_routing(
            operation_no=20,
            operation_name="Robot Welding",
            process_type="ROBOT",
            machine_type="ROBOT",
            cycle_time_sec=72,
            remark="Second operation",
        )
        self._create_routing(
            operation_no=30,
            operation_name="Final Inspection",
            process_type="INSPECTION",
            machine_type="CNC",
            cycle_time_sec=54,
            remark="Final quality inspection",
        )

        work_order = self._create_work_order()

        self.assertEqual(
            work_order.status,
            "RELEASED",
        )

        # ------------------------------------------------------
        # Generate real Production Orders from Routing
        # ------------------------------------------------------
        result = self.generator.generate(
            self.WORK_ORDER_NO,
            auto_commit=False,
        )

        self.session.flush()

        self.assertTrue(result["success"])
        self.assertEqual(result["routing_count"], 3)
        self.assertEqual(result["created_count"], 3)
        self.assertEqual(result["skipped_count"], 0)
        self.assertEqual(result["last_operation_no"], 30)

        production_orders = (
            self.production_order_service.get_by_work_order(
                self.WORK_ORDER_NO
            )
        )

        production_orders = sorted(
            production_orders,
            key=lambda item: item.operation_no,
        )

        self.assertEqual(
            len(production_orders),
            3,
        )
        self.assertEqual(
            [
                item.operation_no
                for item in production_orders
            ],
            [10, 20, 30],
        )

        op10, op20, op30 = production_orders

        # ------------------------------------------------------
        # Verify generated order metadata and sequence
        # ------------------------------------------------------
        for production_order in production_orders:
            self.assertEqual(
                production_order.status,
                "PLANNED",
            )
            self.assertEqual(
                production_order.product_code,
                self.PRODUCT_CODE,
            )
            self.assertEqual(
                production_order.plan_qty,
                self.PLAN_QTY,
            )
            self.assertEqual(
                production_order.completed_qty,
                0,
            )
            self.assertEqual(
                production_order.ng_qty,
                0,
            )

        self.assertEqual(
            op10.planned_start,
            datetime(2026, 7, 28, 8, 0),
        )
        self.assertEqual(
            op10.planned_finish,
            datetime(2026, 7, 28, 9, 0),
        )

        self.assertEqual(
            op20.planned_start,
            op10.planned_finish,
        )
        self.assertEqual(
            op20.planned_finish,
            datetime(2026, 7, 28, 11, 0),
        )

        self.assertEqual(
            op30.planned_start,
            op20.planned_finish,
        )
        self.assertEqual(
            op30.planned_finish,
            datetime(2026, 7, 28, 12, 30),
        )

        self.assertNotIn(
            "FINAL_OPERATION",
            op10.remark or "",
        )
        self.assertNotIn(
            "FINAL_OPERATION",
            op20.remark or "",
        )
        self.assertIn(
            "FINAL_OPERATION",
            op30.remark or "",
        )

        # ------------------------------------------------------
        # Create independent resources for each operation
        # ------------------------------------------------------
        machines = [
            MachineFactory.create_running(
                self.session,
                machine_type="CNC",
                machine_name="OP10 CNC Machine",
            ),
            MachineFactory.create_running(
                self.session,
                machine_type="ROBOT",
                machine_name="OP20 Robot",
            ),
            MachineFactory.create_running(
                self.session,
                machine_type="CNC",
                machine_name="OP30 Inspection Machine",
            ),
        ]

        employees = [
            EmployeeFactory.create_active(
                self.session,
                employee_name="OP10 Operator",
            ),
            EmployeeFactory.create_active(
                self.session,
                employee_name="OP20 Operator",
            ),
            EmployeeFactory.create_active(
                self.session,
                employee_name="OP30 Inspector",
                position="INSPECTOR",
            ),
        ]

        self.session.flush()

        self.assertEqual(
            len(
                {
                    machine.machine_code
                    for machine in machines
                }
            ),
            3,
        )
        self.assertEqual(
            len(
                {
                    employee.employee_code
                    for employee in employees
                }
            ),
            3,
        )

        # ------------------------------------------------------
        # Start the parent Work Order
        # ------------------------------------------------------
        work_order = self.work_order_service.start_work_order(
            self.WORK_ORDER_NO
        )

        self.session.flush()

        self.assertEqual(
            work_order.status,
            "IN_PROGRESS",
        )

        # ------------------------------------------------------
        # Execute OP10 -> OP20 -> OP30 sequentially
        # ------------------------------------------------------
        completed_flows = [
            self._complete_operation(
                production_order=op10,
                machine=machines[0],
                employee=employees[0],
                actual_start=datetime(2026, 7, 28, 8, 0),
                actual_finish=datetime(2026, 7, 28, 9, 0),
                ok_qty=98,
                ng_qty=2,
                processing_ng_qty=1,
                blank_ng_qty=1,
                downtime_minutes=5,
            ),
            self._complete_operation(
                production_order=op20,
                machine=machines[1],
                employee=employees[1],
                actual_start=datetime(2026, 7, 28, 9, 0),
                actual_finish=datetime(2026, 7, 28, 11, 0),
                ok_qty=97,
                ng_qty=3,
                processing_ng_qty=2,
                blank_ng_qty=1,
                downtime_minutes=10,
            ),
            self._complete_operation(
                production_order=op30,
                machine=machines[2],
                employee=employees[2],
                actual_start=datetime(2026, 7, 28, 11, 0),
                actual_finish=datetime(2026, 7, 28, 12, 30),
                ok_qty=96,
                ng_qty=4,
                processing_ng_qty=2,
                blank_ng_qty=2,
                downtime_minutes=5,
            ),
        ]

        # ------------------------------------------------------
        # Complete the parent Work Order
        # ------------------------------------------------------
        work_order = self.work_order_service.complete_work_order(
            self.WORK_ORDER_NO
        )

        self.session.flush()

        self.assertEqual(
            work_order.status,
            "COMPLETED",
        )

        # ------------------------------------------------------
        # Reload every entity through service query APIs
        # ------------------------------------------------------
        persisted_order_ids = set()
        persisted_assignment_ids = set()
        persisted_execution_ids = set()

        expected_results = [
            (10, 98, 2),
            (20, 97, 3),
            (30, 96, 4),
        ]

        for flow, expected in zip(
            completed_flows,
            expected_results,
            strict=True,
        ):
            operation_no, expected_ok, expected_ng = expected

            production_order = flow["production_order"]
            assignment = flow["assignment"]
            execution = flow["execution"]

            persisted_order = (
                self.production_order_service.get_production_order(
                    self.WORK_ORDER_NO,
                    operation_no,
                )
            )
            persisted_assignment = (
                self.assignment_service.get_assignment(
                    assignment.id
                )
            )
            persisted_execution = (
                self.execution_service.get_execution(
                    execution.id
                )
            )

            self.assertIsNotNone(persisted_order)
            self.assertIsNotNone(persisted_assignment)
            self.assertIsNotNone(persisted_execution)

            self.assertEqual(
                persisted_order.status,
                "COMPLETED",
            )
            self.assertEqual(
                persisted_assignment.status,
                "COMPLETED",
            )
            self.assertEqual(
                persisted_execution.status,
                "COMPLETED",
            )

            self.assertEqual(
                persisted_order.completed_qty,
                expected_ok,
            )
            self.assertEqual(
                persisted_order.ng_qty,
                expected_ng,
            )
            self.assertEqual(
                persisted_execution.ok_qty,
                expected_ok,
            )
            self.assertEqual(
                persisted_execution.ng_qty,
                expected_ng,
            )
            self.assertEqual(
                persisted_order.completed_qty,
                persisted_execution.ok_qty,
            )
            self.assertEqual(
                persisted_order.ng_qty,
                persisted_execution.ng_qty,
            )

            persisted_order_ids.add(
                persisted_order.id
            )
            persisted_assignment_ids.add(
                persisted_assignment.id
            )
            persisted_execution_ids.add(
                persisted_execution.id
            )

            self.assertEqual(
                persisted_assignment.production_order_id,
                production_order.id,
            )
            self.assertEqual(
                persisted_execution.assignment_id,
                persisted_assignment.id,
            )

        # Each operation must own independent database records.
        self.assertEqual(
            len(persisted_order_ids),
            3,
        )
        self.assertEqual(
            len(persisted_assignment_ids),
            3,
        )
        self.assertEqual(
            len(persisted_execution_ids),
            3,
        )

        persisted_work_order = (
            self.work_order_service.get_work_order(
                self.WORK_ORDER_NO
            )
        )

        self.assertIsNotNone(persisted_work_order)
        self.assertEqual(
            persisted_work_order.status,
            "COMPLETED",
        )