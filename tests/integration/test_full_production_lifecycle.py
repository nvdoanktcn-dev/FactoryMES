from __future__ import annotations

from datetime import date, datetime

from tests.base.database_test_case import DatabaseTestCase
from tests.factories.employee_factory import EmployeeFactory
from tests.factories.machine_factory import MachineFactory

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


class TestFullProductionLifecycle(DatabaseTestCase):
    """Verify planning-to-execution production lifecycle."""

    def test_full_production_lifecycle_from_generator(self):
        product_code = "INT-LIFE-001"
        work_order_no = "WO-INT-LIFE-001"

        product_service = ProductService(
            session=self.session,
        )
        routing_service = RoutingService(
            session=self.session,
        )
        work_order_service = WorkOrderService(
            session=self.session,
        )
        production_order_service = ProductionOrderService(
            session=self.session,
        )
        assignment_service = ProductionAssignmentService(
            session=self.session,
        )
        execution_service = ProductionExecutionService(
            session=self.session,
        )
        generator = ProductionOrderGenerator(
            session=self.session,
        )

        # ------------------------------------------------------
        # Step 1: create production master data
        # ------------------------------------------------------
        product = product_service.create_product(
            product_code=product_code,
            product_name_vi="Full Lifecycle Integration Product",
            customer="INTEGRATION CUSTOMER",
            material="STEEL",
            unit="PCS",
            status="ACTIVE",
        )

        routing = routing_service.create_routing(
            {
                "product_code": product_code,
                "operation_no": 10,
                "operation_name": "CNC Machining",
                "process_type": "CNC",
                "machine_type": "CNC",
                "standard_cycle_time_sec": 36,
                "standard_output_pcs_hour": 100,
                "standard_operator_count": 1,
                "status": "ACTIVE",
                "remark": "Lifecycle routing",
            }
        )

        self.session.flush()

        self.assertEqual(product.product_code, product_code)
        self.assertEqual(routing.operation_no, 10)
        self.assertEqual(routing.status, "ACTIVE")

        # ------------------------------------------------------
        # Step 2: create and release the Work Order
        # ------------------------------------------------------
        work_order = work_order_service.create_work_order(
            {
                "work_order_no": work_order_no,
                "product_code": product_code,
                "plan_qty": 100,
                "start_date": date(2026, 7, 28),
                "due_date": date(2026, 8, 28),
                "priority": "NORMAL",
                "status": "PLANNED",
                "remark": "Full production lifecycle",
            }
        )

        work_order = work_order_service.release_work_order(
            work_order_no
        )

        self.session.flush()

        self.assertEqual(work_order.status, "RELEASED")

        # ------------------------------------------------------
        # Step 3: generate the real Production Order
        # ------------------------------------------------------
        generation_result = generator.generate(
            work_order_no,
            auto_commit=False,
        )

        self.session.flush()

        self.assertTrue(generation_result["success"])
        self.assertEqual(generation_result["routing_count"], 1)
        self.assertEqual(generation_result["created_count"], 1)
        self.assertEqual(generation_result["skipped_count"], 0)
        self.assertEqual(generation_result["last_operation_no"], 10)

        generated_orders = (
            production_order_service.get_by_work_order(
                work_order_no
            )
        )

        self.assertEqual(len(generated_orders), 1)

        production_order = generated_orders[0]

        self.assertIsNotNone(production_order.id)
        self.assertEqual(
            production_order.work_order_no,
            work_order_no,
        )
        self.assertEqual(
            production_order.product_code,
            product_code,
        )
        self.assertEqual(production_order.operation_no, 10)
        self.assertEqual(production_order.plan_qty, 100)
        self.assertEqual(production_order.status, "PLANNED")
        self.assertIn(
            "FINAL_OPERATION",
            production_order.remark or "",
        )
        self.assertEqual(
            production_order.planned_start,
            datetime(2026, 7, 28, 8, 0),
        )
        self.assertEqual(
            production_order.planned_finish,
            datetime(2026, 7, 28, 9, 0),
        )

        generated_production_order_id = production_order.id

        # ------------------------------------------------------
        # Step 4: create production resources
        # ------------------------------------------------------
        machine = MachineFactory.create_running(
            self.session,
        )
        employee = EmployeeFactory.create_active(
            self.session,
        )

        self.session.flush()

        self.assertIsNotNone(machine.id)
        self.assertIsNotNone(employee.id)

        # ------------------------------------------------------
        # Step 5: release Production Order
        # ------------------------------------------------------
        production_order = production_order_service.release(
            work_order_no,
            production_order.operation_no,
        )

        self.session.flush()

        self.assertEqual(production_order.status, "RELEASED")

        # ------------------------------------------------------
        # Step 6: create and release resource assignment
        # ------------------------------------------------------
        assignment = assignment_service.create_assignment(
            {
                "production_order_id": production_order.id,
                "machine_code": machine.machine_code,
                "employee_code": employee.employee_code,
                "shift": "DAY",
                "planned_start": (
                    production_order.planned_start
                ),
                "planned_finish": (
                    production_order.planned_finish
                ),
                "status": "DRAFT",
                "assigned_at": None,
                "released_at": None,
                "actual_start": None,
                "actual_finish": None,
                "remark": "Full lifecycle assignment",
            }
        )

        self.session.flush()

        self.assertIsNotNone(assignment.id)
        self.assertEqual(assignment.status, "DRAFT")
        self.assertEqual(
            assignment.production_order_id,
            generated_production_order_id,
        )
        self.assertEqual(
            assignment.machine_code,
            machine.machine_code,
        )
        self.assertEqual(
            assignment.employee_code,
            employee.employee_code,
        )
        self.assertEqual(assignment.shift, "DAY")

        assignment = assignment_service.release(
            assignment.id
        )

        self.session.flush()

        self.assertEqual(assignment.status, "RELEASED")
        self.assertIsNotNone(assignment.released_at)

        # ------------------------------------------------------
        # Step 7: start Work Order, Production Order,
        #         and Assignment
        # ------------------------------------------------------
        actual_start = datetime(2026, 7, 28, 8, 0)

        work_order = work_order_service.start_work_order(
            work_order_no
        )

        production_order = production_order_service.start(
            work_order_no,
            production_order.operation_no,
            actual_start=actual_start,
        )

        assignment = assignment_service.start(
            assignment.id,
            actual_start=actual_start,
        )

        self.session.flush()

        self.assertEqual(work_order.status, "IN_PROGRESS")
        self.assertEqual(
            production_order.status,
            "IN_PROGRESS",
        )
        self.assertEqual(assignment.status, "IN_PROGRESS")
        self.assertEqual(
            production_order.actual_start,
            actual_start,
        )
        self.assertEqual(
            assignment.actual_start,
            actual_start,
        )

        # ------------------------------------------------------
        # Step 8: start and complete execution
        # ------------------------------------------------------
        execution = execution_service.start_execution(
            assignment.id,
            start_time=actual_start,
            remark="Full lifecycle execution",
        )

        self.session.flush()

        self.assertIsNotNone(execution.id)
        self.assertEqual(execution.status, "RUNNING")
        self.assertEqual(
            execution.assignment_id,
            assignment.id,
        )

        actual_finish = datetime(2026, 7, 28, 9, 0)

        execution = execution_service.stop_execution(
            execution.id,
            ok_qty=98,
            ng_qty=2,
            processing_ng_qty=1,
            blank_ng_qty=1,
            downtime_minutes=10,
            end_time=actual_finish,
            complete=True,
        )

        self.session.flush()

        self.assertEqual(execution.status, "COMPLETED")
        self.assertEqual(execution.ok_qty, 98)
        self.assertEqual(execution.ng_qty, 2)
        self.assertEqual(execution.processing_ng_qty, 1)
        self.assertEqual(execution.blank_ng_qty, 1)
        self.assertEqual(execution.downtime_minutes, 10)
        self.assertEqual(execution.runtime_minutes, 50)
        self.assertEqual(execution.end_time, actual_finish)

        # ------------------------------------------------------
        # Step 9: complete assignment, Production Order,
        #         and Work Order
        # ------------------------------------------------------
        assignment = assignment_service.complete(
            assignment.id,
            actual_finish=actual_finish,
        )

        production_order = production_order_service.complete(
            work_order_no,
            production_order.operation_no,
            completed_qty=execution.ok_qty,
            ng_qty=execution.ng_qty,
            actual_finish=actual_finish,
        )

        work_order = work_order_service.complete_work_order(
            work_order_no
        )

        self.session.flush()

        self.assertEqual(assignment.status, "COMPLETED")
        self.assertEqual(
            assignment.actual_finish,
            actual_finish,
        )

        self.assertEqual(
            production_order.status,
            "COMPLETED",
        )
        self.assertEqual(production_order.completed_qty, 98)
        self.assertEqual(production_order.ng_qty, 2)
        self.assertEqual(
            production_order.actual_finish,
            actual_finish,
        )

        self.assertEqual(work_order.status, "COMPLETED")

        # ------------------------------------------------------
        # Step 10: reload through repository-backed APIs
        # ------------------------------------------------------
        persisted_work_order = (
            work_order_service.get_work_order(
                work_order_no
            )
        )
        persisted_production_order = (
            production_order_service.get_production_order(
                work_order_no,
                10,
            )
        )
        persisted_assignment = (
            assignment_service.get_assignment(
                assignment.id
            )
        )
        persisted_execution = (
            execution_service.get_execution(
                execution.id
            )
        )

        self.assertIsNotNone(persisted_work_order)
        self.assertIsNotNone(persisted_production_order)
        self.assertIsNotNone(persisted_assignment)
        self.assertIsNotNone(persisted_execution)

        self.assertEqual(
            persisted_work_order.status,
            "COMPLETED",
        )
        self.assertEqual(
            persisted_production_order.status,
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
            persisted_production_order.id,
            generated_production_order_id,
        )
        self.assertEqual(
            persisted_assignment.production_order_id,
            generated_production_order_id,
        )
        self.assertEqual(
            persisted_execution.assignment_id,
            persisted_assignment.id,
        )

        self.assertEqual(
            persisted_production_order.completed_qty,
            persisted_execution.ok_qty,
        )
        self.assertEqual(
            persisted_production_order.ng_qty,
            persisted_execution.ng_qty,
        )
        self.assertIn(
            "FINAL_OPERATION",
            persisted_production_order.remark or "",
        )
