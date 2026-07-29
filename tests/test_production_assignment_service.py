from tests.base_db_test import DatabaseTestCase
from tests.factories.production_assignment_factory import (
    ProductionAssignmentFactory,
)

from src.services.production_assignment_service import (
    ProductionAssignmentService,
)
from tests.factories.employee_factory import (
    EmployeeFactory,
)
from tests.factories.machine_factory import (
    MachineFactory,
)
from tests.factories.production_execution_factory import (
    ProductionExecutionFactory,
)

class TestProductionAssignmentService(DatabaseTestCase):

    def setUp(self):
        super().setUp()

        self.service = ProductionAssignmentService(
            session=self.session
        )

    def test_create_assignment(self):
        assignment = ProductionAssignmentFactory.create(
            self.session,
            remark="Assignment service test",
        )

        self.assertIsNotNone(assignment)
        self.assertIsNotNone(assignment.id)
        self.assertIsNotNone(assignment.production_order_id)
        self.assertEqual(assignment.status, "DRAFT")
        self.assertEqual(
            assignment.remark,
            "Assignment service test",
        )

    def test_create_assignment_creates_history(self):
        assignment = ProductionAssignmentFactory.create(
            self.session,
            remark="Assignment history test",
        )

        histories = (
            self.service.history_service
            .get_by_assignment_id(assignment.id)
        )

        self.assertTrue(histories)
        self.assertEqual(histories[0].action, "CREATE")
        self.assertEqual(histories[0].new_status, "DRAFT")

    def _create_release_ready_assignment(self):
        machine = MachineFactory.create_running(
            self.session
        )

        employee = EmployeeFactory.create_active(
            self.session
        )

        assignment = ProductionAssignmentFactory.create_draft(
            self.session,
            machine_code=machine.machine_code,
            employee_code=employee.employee_code,
            shift="DAY",
        )

        return assignment

    def test_release_success(self):
        assignment = (
            self._create_release_ready_assignment()
        )

        result = self.service.release(
            assignment.id
        )

        self.session.flush()

        self.assertEqual(
            result.status,
            "RELEASED",
        )
        self.assertIsNotNone(
            result.released_at
        )

        histories = (
            self.service.history_service
            .get_by_assignment_id(
                assignment.id
            )
        )

        latest = histories[0]

        self.assertEqual(
            latest.action,
            "RELEASE",
        )
        self.assertEqual(
            latest.new_status,
            "RELEASED",
        )

    def test_release_requires_employee(self):
        machine = MachineFactory.create_running(
            self.session
        )

        assignment = ProductionAssignmentFactory.create_draft(
            self.session,
            machine_code=machine.machine_code,
            employee_code=None,
            shift="DAY",
        )

        with self.assertRaisesRegex(
            ValueError,
            "Employee must be assigned",
        ):
            self.service.release(
                assignment.id
            )

    def test_release_requires_machine(self):
        employee = EmployeeFactory.create_active(
            self.session
        )

        production_order = (
            ProductionAssignmentFactory
            .get_production_order(
                self.session
            )
        )

        if not production_order.machine_type:
            self.skipTest(
                "ProductionOrder has no machine_type."
            )

        assignment = ProductionAssignmentFactory.create_draft(
            self.session,
            machine_code=None,
            employee_code=employee.employee_code,
            shift="DAY",
        )

        with self.assertRaisesRegex(
            ValueError,
            "Machine must be assigned",
        ):
            self.service.release(
                assignment.id
            )

    def test_release_requires_shift(self):
        machine = MachineFactory.create_running(
            self.session
        )

        employee = EmployeeFactory.create_active(
            self.session
        )

        assignment = ProductionAssignmentFactory.create_draft(
            self.session,
            machine_code=machine.machine_code,
            employee_code=employee.employee_code,
            shift=None,
        )

        with self.assertRaisesRegex(
            ValueError,
            "Shift must be assigned",
        ):
            self.service.release(
                assignment.id
            )

    def test_release_wrong_status(self):
        assignment = ProductionAssignmentFactory.create_completed(
            self.session
        )

        with self.assertRaisesRegex(
            ValueError,
            "Only DRAFT or ON_HOLD",
        ):
            self.service.release(
                assignment.id
            )

    def test_start_success(self):
        assignment = (
            self._create_release_ready_assignment()
        )

        self.service.release(
            assignment.id
        )

        result = self.service.start(
            assignment.id,
            actual_start="2026-07-20 08:05",
        )

        self.session.flush()

        self.assertEqual(
            result.status,
            "IN_PROGRESS",
        )
        self.assertEqual(
            result.actual_start.strftime(
                "%Y-%m-%d %H:%M"
            ),
            "2026-07-20 08:05",
        )

        histories = (
            self.service.history_service
            .get_by_assignment_id(
                assignment.id
            )
        )

        latest = histories[0]

        self.assertEqual(
            latest.action,
            "START",
        )
        self.assertEqual(
            latest.new_status,
            "IN_PROGRESS",
        )

    def test_start_requires_released(self):
        assignment = (
            ProductionAssignmentFactory
            .create_draft(
                self.session
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "Only RELEASED assignments",
        ):
            self.service.start(
                assignment.id
            )

    def test_hold_success(self):
        assignment = (
            self._create_release_ready_assignment()
        )

        self.service.release(
            assignment.id
        )

        self.service.start(
            assignment.id
        )

        result = self.service.hold(
            assignment.id
        )

        self.session.flush()

        self.assertEqual(
            result.status,
            "ON_HOLD",
        )

        histories = (
            self.service.history_service
            .get_by_assignment_id(
                assignment.id
            )
        )

        latest = histories[0]

        self.assertEqual(
            latest.action,
            "HOLD",
        )
        self.assertEqual(
            latest.new_status,
            "ON_HOLD",
        )

    def test_hold_wrong_status(self):
        assignment = (
            ProductionAssignmentFactory
            .create_draft(
                self.session
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "Only IN_PROGRESS assignments",
        ):
            self.service.hold(
                assignment.id
            )

    def test_complete_from_in_progress(self):
        assignment = (
            self._create_release_ready_assignment()
        )

        self.service.release(
            assignment.id
        )

        self.service.start(
            assignment.id,
            actual_start="2026-07-20 08:00",
        )

        ProductionExecutionFactory.create_stopped(
            self.session,
            assignment,
        )

        result = self.service.complete(
            assignment.id,
            actual_finish="2026-07-20 12:00",
        )

        self.session.flush()

        self.assertEqual(
            result.status,
            "COMPLETED",
        )
        self.assertEqual(
            result.actual_finish.strftime(
                "%Y-%m-%d %H:%M"
            ),
            "2026-07-20 12:00",
        )

    def test_complete_from_on_hold(self):
        assignment = (
            self._create_release_ready_assignment()
        )

        self.service.release(
            assignment.id
        )

        self.service.start(
            assignment.id
        )
        ProductionExecutionFactory.create_stopped(
            self.session,
            assignment,
        )

        self.service.hold(
            assignment.id
        )

        result = self.service.complete(
            assignment.id
        )

        self.session.flush()

        self.assertEqual(
            result.status,
            "COMPLETED",
        )
        self.assertIsNotNone(
            result.actual_finish
        )

        histories = (
            self.service.history_service
            .get_by_assignment_id(
                assignment.id
            )
        )

        latest = histories[0]

        self.assertEqual(
            latest.action,
            "COMPLETE",
        )
        self.assertEqual(
            latest.new_status,
            "COMPLETED",
        )

    def test_complete_wrong_status(self):
        assignment = (
            ProductionAssignmentFactory
            .create_draft(
                self.session
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "Only IN_PROGRESS or ON_HOLD",
        ):
            self.service.complete(
                assignment.id
            )

    def test_cancel_success(self):
        assignment = (
            ProductionAssignmentFactory
            .create_draft(
                self.session
            )
        )

        result = self.service.cancel(
            assignment.id
        )

        self.session.flush()

        self.assertEqual(
            result.status,
            "CANCELLED",
        )

        histories = (
            self.service.history_service
            .get_by_assignment_id(
                assignment.id
            )
        )

        latest = histories[0]

        self.assertEqual(
            latest.action,
            "CANCEL",
        )
        self.assertEqual(
            latest.new_status,
            "CANCELLED",
        )

    def test_cancel_in_progress_rejected(self):
        assignment = (
            ProductionAssignmentFactory
            .create_in_progress(
                self.session
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "cannot be cancelled",
        ):
            self.service.cancel(
                assignment.id
            )

    def test_cancel_completed_rejected(self):
        assignment = (
            ProductionAssignmentFactory
            .create_completed(
                self.session
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "cannot be cancelled",
        ):
            self.service.cancel(
                assignment.id
            )


    def test_create_rejects_machine_time_conflict(self):
        machine = MachineFactory.create_running(self.session)
        emp1 = EmployeeFactory.create_active(self.session)
        emp2 = EmployeeFactory.create_active(self.session)

        ProductionAssignmentFactory.create_draft(
            self.session,
            machine_code=machine.machine_code,
            employee_code=emp1.employee_code,
            shift="DAY",
            planned_start="2026-07-20 08:00",
            planned_finish="2026-07-20 12:00",
        )

        with self.assertRaisesRegex(ValueError, "Assignment time conflict"):
            self.service.create_assignment({
                "production_order_id": ProductionAssignmentFactory.get_production_order(self.session).id,
                "machine_code": machine.machine_code,
                "employee_code": emp2.employee_code,
                "shift": "DAY",
                "planned_start": "2026-07-20 10:00",
                "planned_finish": "2026-07-20 14:00",
            })

    def test_create_rejects_unsupported_shift(self):
        with self.assertRaisesRegex(
            ValueError,
            "Allowed values: DAY, NIGHT",
        ):
            self.service.create_assignment({
                "production_order_id": (
                    ProductionAssignmentFactory
                    .get_production_order(self.session)
                    .id
                ),
                "shift": "OFFICE",
                "planned_start": "2026-07-20 08:00",
                "planned_finish": "2026-07-20 12:00",
            })

    def test_complete_rejects_finish_before_start(self):
        assignment = self._create_release_ready_assignment()
        self.service.release(assignment.id)
        self.service.start(
            assignment.id,
            actual_start="2026-07-20 08:00",
        )

        with self.assertRaisesRegex(
            ValueError,
            "Actual Finish cannot be before Actual Start",
        ):
            self.service.complete(
                assignment.id,
                actual_finish="2026-07-20 07:59",
            )
