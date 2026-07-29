from tests.base.database_test_case import DatabaseTestCase

from src.services.production_assignment_service import (
    ProductionAssignmentService,
)
from src.services.production_execution_service import (
    ProductionExecutionService,
)

from tests.factories.production_assignment_factory import (
    ProductionAssignmentFactory,
)
from tests.factories.production_execution_factory import (
    ProductionExecutionFactory,
)


class TestProductionAssignmentCompletionGuard(
    DatabaseTestCase
):

    def setUp(self):
        super().setUp()

        self.assignment_service = (
            ProductionAssignmentService(
                session=self.session
            )
        )

        self.execution_service = (
            ProductionExecutionService(
                session=self.session
            )
        )

    def test_complete_assignment_with_stopped_execution(self):

        assignment = (
            ProductionAssignmentFactory.create_in_progress(
                self.session
            )
        )

        ProductionExecutionFactory.create_stopped(
            self.session,
            assignment,
        )

        assignment = self.assignment_service.complete(
            assignment.id
        )

        self.assertEqual(
            assignment.status,
            "COMPLETED",
        )

    def test_complete_assignment_with_completed_execution(self):

        assignment = (
            ProductionAssignmentFactory.create_in_progress(
                self.session
            )
        )

        ProductionExecutionFactory.create_completed(
            self.session,
            assignment,
        )

        assignment = self.assignment_service.complete(
            assignment.id
        )

        self.assertEqual(
            assignment.status,
            "COMPLETED",
        )

    def test_rejects_completion_with_running_execution(self):

        assignment = (
            ProductionAssignmentFactory.create_in_progress(
                self.session
            )
        )

        ProductionExecutionFactory.create_running(
            self.session,
            assignment,
        )

        with self.assertRaises(ValueError):
            self.assignment_service.complete(
                assignment.id
            )

        assignment = (
            self.assignment_service.get_assignment(
                assignment.id
            )
        )

        self.assertEqual(
            assignment.status,
            "IN_PROGRESS",
        )

    def test_rejects_completion_without_executions(self):

        assignment = (
            ProductionAssignmentFactory.create_in_progress(
                self.session
            )
        )

        with self.assertRaises(ValueError):
            self.assignment_service.complete(
                assignment.id
            )

        assignment = (
            self.assignment_service.get_assignment(
                assignment.id
            )
        )

        self.assertEqual(
            assignment.status,
            "IN_PROGRESS",
        )

    def test_rejects_completion_with_only_cancelled_executions(self):

        assignment = (
            ProductionAssignmentFactory.create_in_progress(
                self.session
            )
        )

        ProductionExecutionFactory.create_cancelled(
            self.session,
            assignment,
        )

        with self.assertRaises(ValueError):
            self.assignment_service.complete(
                assignment.id
            )

        assignment = (
            self.assignment_service.get_assignment(
                assignment.id
            )
        )

        self.assertEqual(
            assignment.status,
            "IN_PROGRESS",
        )

    def test_failed_completion_preserves_assignment_status(self):

        assignment = (
            ProductionAssignmentFactory.create_in_progress(
                self.session
            )
        )

        ProductionExecutionFactory.create_running(
            self.session,
            assignment,
        )

        with self.assertRaises(ValueError):
            self.assignment_service.complete(
                assignment.id
            )

        assignment = (
            self.assignment_service.get_assignment(
                assignment.id
            )
        )

        self.assertEqual(
            assignment.status,
            "IN_PROGRESS",
        )

        self.assertIsNotNone(
            assignment.actual_start
        )

        self.assertIsNone(
            assignment.actual_finish
        )