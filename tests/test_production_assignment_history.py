from tests.base_db_test import DatabaseTestCase
from tests.factories.production_assignment_factory import (
    ProductionAssignmentFactory,
)

from src.services.production_assignment_service import (
    ProductionAssignmentService,
)


class TestProductionAssignmentHistory(DatabaseTestCase):

    def setUp(self):
        super().setUp()

        self.service = ProductionAssignmentService(
            session=self.session
        )

    def test_create_assignment_records_history(self):
        assignment = ProductionAssignmentFactory.create(
            self.session,
            remark="Dedicated history test",
        )

        histories = (
            self.service.history_service
            .get_by_assignment_id(assignment.id)
        )

        self.assertEqual(len(histories), 1)

        history = histories[0]

        self.assertEqual(history.assignment_id, assignment.id)
        self.assertEqual(history.action, "CREATE")
        self.assertEqual(history.new_status, "DRAFT")

    def test_history_belongs_to_correct_assignment(self):
        first_assignment = ProductionAssignmentFactory.create(
            self.session,
            remark="First history assignment",
        )

        second_assignment = ProductionAssignmentFactory.create(
            self.session,
            remark="Second history assignment",
        )

        first_histories = (
            self.service.history_service
            .get_by_assignment_id(first_assignment.id)
        )

        second_histories = (
            self.service.history_service
            .get_by_assignment_id(second_assignment.id)
        )

        self.assertTrue(first_histories)
        self.assertTrue(second_histories)

        self.assertTrue(
            all(
                item.assignment_id == first_assignment.id
                for item in first_histories
            )
        )

        self.assertTrue(
            all(
                item.assignment_id == second_assignment.id
                for item in second_histories
            )
        )