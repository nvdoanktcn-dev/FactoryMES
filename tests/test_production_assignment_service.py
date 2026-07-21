from tests.base_db_test import DatabaseTestCase
from tests.factories.production_assignment_factory import (
    ProductionAssignmentFactory,
)

from src.services.production_assignment_service import (
    ProductionAssignmentService,
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