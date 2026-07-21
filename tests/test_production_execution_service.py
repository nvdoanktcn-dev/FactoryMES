from tests.base_db_test import DatabaseTestCase

from src.models.production_assignment import ProductionAssignment
from src.services.production_execution_service import (
    ProductionExecutionService,
)


class TestProductionExecutionService(DatabaseTestCase):

    def setUp(self):
        super().setUp()

        self.service = ProductionExecutionService(
            session=self.session
        )

    def get_available_assignment(self):
        """
        Lấy Assignment đang IN_PROGRESS nhưng chưa có
        ProductionExecution ở trạng thái RUNNING.
        """

        assignments = (
            self.session
            .query(ProductionAssignment)
            .filter(
                ProductionAssignment.status == "IN_PROGRESS"
            )
            .order_by(ProductionAssignment.id.asc())
            .all()
        )

        for assignment in assignments:
            running_execution = (
                self.service.repository
                .get_running_by_assignment_id(assignment.id)
            )

            if running_execution is None:
                return assignment

        self.skipTest(
            (
                "Không có Assignment IN_PROGRESS phù hợp. "
                "Hãy release và start một Assignment trước."
            )
        )

    def test_start_and_stop_execution(self):
        assignment = self.get_available_assignment()

        execution = self.service.start_execution(
            assignment.id,
            start_time="2026-07-20 08:00",
            remark="Execution service test",
        )

        self.session.flush()

        self.assertIsNotNone(execution)
        self.assertIsNotNone(execution.id)

        self.assertEqual(
            execution.assignment_id,
            assignment.id,
        )

        self.assertEqual(
            execution.status,
            "RUNNING",
        )

        execution = self.service.stop_execution(
            execution.id,
            ok_qty=95,
            ng_qty=5,
            processing_ng_qty=3,
            blank_ng_qty=2,
            downtime_minutes=30,
            end_time="2026-07-20 12:00",
            complete=True,
        )

        self.session.flush()

        self.assertEqual(execution.ok_qty, 95)
        self.assertEqual(execution.ng_qty, 5)
        self.assertEqual(execution.processing_ng_qty, 3)
        self.assertEqual(execution.blank_ng_qty, 2)
        self.assertEqual(execution.downtime_minutes, 30)

        # 08:00–12:00 = 240 phút
        # Trừ 30 phút downtime = 210 phút runtime
        self.assertEqual(execution.runtime_minutes, 210)

        self.assertEqual(
            execution.status,
            "COMPLETED",
        )