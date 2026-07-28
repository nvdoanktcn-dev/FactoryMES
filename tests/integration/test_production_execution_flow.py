from datetime import datetime

from tests.base.database_test_case import DatabaseTestCase
from tests.factories.employee_factory import EmployeeFactory
from tests.factories.machine_factory import MachineFactory
from tests.factories.production_assignment_factory import (
    ProductionAssignmentFactory,
)
from tests.factories.production_order_factory import (
    ProductionOrderFactory,
)

from src.services.production_assignment_service import (
    ProductionAssignmentService,
)
from src.services.production_execution_service import (
    ProductionExecutionService,
)
from src.services.production_order_service import (
    ProductionOrderService,
)


class TestProductionExecutionFlow(DatabaseTestCase):
    """Verify the core production order-to-execution lifecycle."""

    def test_complete_production_execution_flow(self):
        # ------------------------------------------------------
        # Arrange: create the production resources
        # ------------------------------------------------------
        machine = MachineFactory.create_running(
            self.session,
        )

        employee = EmployeeFactory.create_active(
            self.session,
        )

        production_order = ProductionOrderFactory.create(
            self.session,
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

        # ------------------------------------------------------
        # Step 1: release the operation-level production order
        # ------------------------------------------------------
        production_order = production_order_service.release(
            production_order.work_order_no,
            production_order.operation_no,
        )

        self.session.flush()

        assert production_order.status == "RELEASED"

        # ------------------------------------------------------
        # Step 2: create a draft resource assignment
        # ------------------------------------------------------
        assignment = ProductionAssignmentFactory.create_draft(
            self.session,
            production_order=production_order,
            machine_code=machine.machine_code,
            employee_code=employee.employee_code,
            shift="DAY",
            planned_start=datetime(2026, 7, 20, 8, 0),
            planned_finish=datetime(2026, 7, 20, 20, 0),
        )

        assert assignment.status == "DRAFT"
        assert assignment.production_order_id == production_order.id
        assert assignment.machine_code == machine.machine_code
        assert assignment.employee_code == employee.employee_code
        assert assignment.shift == "DAY"

        # ------------------------------------------------------
        # Step 3: release the assignment
        # ------------------------------------------------------
        assignment = assignment_service.release(
            assignment.id,
        )

        self.session.flush()

        assert assignment.status == "RELEASED"
        assert assignment.released_at is not None

        # ------------------------------------------------------
        # Step 4: start the production order and assignment
        # ------------------------------------------------------
        production_order = production_order_service.start(
            production_order.work_order_no,
            production_order.operation_no,
            actual_start=datetime(2026, 7, 20, 8, 0),
        )

        assignment = assignment_service.start(
            assignment.id,
            actual_start=datetime(2026, 7, 20, 8, 0),
        )

        self.session.flush()

        assert production_order.status == "IN_PROGRESS"
        assert assignment.status == "IN_PROGRESS"
        assert assignment.actual_start is not None

        # ------------------------------------------------------
        # Step 5: start a production execution
        # ------------------------------------------------------
        execution = execution_service.start_execution(
            assignment.id,
            start_time=datetime(2026, 7, 20, 8, 0),
            remark="Integration production flow",
        )

        self.session.flush()

        assert execution.id is not None
        assert execution.assignment_id == assignment.id
        assert execution.status == "RUNNING"
        assert execution.start_time == datetime(
            2026,
            7,
            20,
            8,
            0,
        )

        # ------------------------------------------------------
        # Step 6: stop and complete the execution
        # ------------------------------------------------------
        execution = execution_service.stop_execution(
            execution.id,
            ok_qty=98,
            ng_qty=2,
            processing_ng_qty=1,
            blank_ng_qty=1,
            downtime_minutes=10,
            end_time=datetime(2026, 7, 20, 12, 0),
            complete=True,
        )

        self.session.flush()

        assert execution.status == "COMPLETED"
        assert execution.ok_qty == 98
        assert execution.ng_qty == 2
        assert execution.processing_ng_qty == 1
        assert execution.blank_ng_qty == 1
        assert execution.downtime_minutes == 10
        assert execution.end_time == datetime(
            2026,
            7,
            20,
            12,
            0,
        )

        # ------------------------------------------------------
        # Step 7: complete assignment and production order
        # ------------------------------------------------------
        assignment = assignment_service.complete(
            assignment.id,
            actual_finish=datetime(2026, 7, 20, 12, 0),
        )

        production_order = production_order_service.complete(
            production_order.work_order_no,
            production_order.operation_no,
            completed_qty=98,
            ng_qty=2,
        )

        self.session.flush()

        assert assignment.status == "COMPLETED"
        assert assignment.actual_finish is not None

        assert production_order.status == "COMPLETED"
        assert production_order.completed_qty == 98
        assert production_order.ng_qty == 2

        # ------------------------------------------------------
        # Step 8: verify persistence through repository-backed APIs
        # ------------------------------------------------------
        persisted_assignment = assignment_service.get_assignment(
            assignment.id,
        )

        persisted_execution = execution_service.get_execution(
            execution.id,
        )

        persisted_order = (
            production_order_service.get_production_order(
                production_order.work_order_no,
                production_order.operation_no,
            )
        )

        assert persisted_assignment is not None
        assert persisted_assignment.status == "COMPLETED"

        assert persisted_execution is not None
        assert persisted_execution.status == "COMPLETED"

        assert persisted_order is not None
        assert persisted_order.status == "COMPLETED"