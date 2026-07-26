from datetime import timedelta

from tests.base_db_test import DatabaseTestCase

from src.models.production_assignment import ProductionAssignment
from src.services.production_execution_service import (
    ProductionExecutionService,
)
from src.services.production_downtime_service import (
    ProductionDowntimeService,
)


class TestProductionDowntimeService(DatabaseTestCase):

    def setUp(self):
        super().setUp()

        self.execution_service = ProductionExecutionService(
            session=self.session
        )

        self.downtime_service = ProductionDowntimeService(
            session=self.session
        )

    def get_running_execution(self):

        assignment = (
            self.session.query(ProductionAssignment)
            .filter(
                ProductionAssignment.status == "IN_PROGRESS"
            )
            .order_by(
                ProductionAssignment.id.asc()
            )
            .first()
        )

        if assignment is None:
            self.skipTest(
                "Không có Assignment IN_PROGRESS."
            )

        execution = (
            self.execution_service.repository
            .get_running_by_assignment_id(
                assignment.id
            )
        )

        if execution is None:

            execution = (
                self.execution_service.start_execution(
                    assignment.id,
                    start_time="2026-07-20 08:00",
                    remark="Downtime Test",
                )
            )

            self.session.flush()

        return execution

    def test_start_downtime(self):

        execution = self.get_running_execution()

        event = (
            self.downtime_service.start_downtime(
                execution.id,
                "WAIT_MATERIAL",
                start_time="2026-07-20 09:00",
                remark="Waiting material",
            )
        )

        self.session.flush()

        self.assertIsNotNone(event.id)

        self.assertEqual(
            event.status,
            "OPEN",
        )

        self.assertEqual(
            event.reason_code,
            "WAIT_MATERIAL",
        )

    def test_stop_downtime(self):

        execution = self.get_running_execution()

        existing = (
            self.downtime_service.repository
            .get_open_by_execution_id(
                execution.id
            )
        )

        if existing:

            existing.status = "CANCELLED"
            existing.duration_minutes = 0

            self.session.flush()

        event = (
            self.downtime_service.start_downtime(
                execution.id,
                "WAIT_MATERIAL",
                start_time="2026-07-20 09:00",
            )
        )

        self.session.flush()

        event = (
            self.downtime_service.stop_downtime(
                event.id,
                end_time="2026-07-20 09:30",
            )
        )

        self.session.flush()

        self.assertEqual(
            event.status,
            "CLOSED",
        )

        self.assertEqual(
            event.duration_minutes,
            30,
        )

    def test_execution_downtime_updated(self):

        execution = self.get_running_execution()

        existing = (
            self.downtime_service.repository
            .get_open_by_execution_id(
                execution.id
            )
        )

        if existing:

            existing.status = "CANCELLED"
            existing.duration_minutes = 0

            self.session.flush()

        event = (
            self.downtime_service.start_downtime(
                execution.id,
                "WAIT_MATERIAL",
                start_time="2026-07-20 09:00",
            )
        )

        self.session.flush()

        self.downtime_service.stop_downtime(
            event.id,
            end_time="2026-07-20 09:30",
        )

        self.session.flush()

        refreshed = (
            self.execution_service.get_execution(
                execution.id
            )
        )

        self.assertGreaterEqual(
            refreshed.downtime_minutes,
            30,
        )

    def test_start_rejects_time_before_execution(self):
        execution = self.get_running_execution()

        with self.assertRaisesRegex(
            ValueError,
            "cannot be before Execution Start Time",
        ):
            self.downtime_service.start_downtime(
                execution.id,
                "WAIT_MATERIAL",
                start_time=(
                    execution.start_time
                    - timedelta(minutes=1)
                ),
            )

    def test_start_rejects_overlap_with_closed_downtime(self):
        execution = self.get_running_execution()
        first_start = (
            execution.start_time
            + timedelta(hours=1)
        )
        first = self.downtime_service.start_downtime(
            execution.id,
            "WAIT_MATERIAL",
            start_time=first_start,
        )
        self.downtime_service.stop_downtime(
            first.id,
            end_time=(
                first_start
                + timedelta(minutes=30)
            ),
        )

        with self.assertRaisesRegex(
            ValueError,
            "Start Time overlaps",
        ):
            self.downtime_service.start_downtime(
                execution.id,
                "WAIT_OPERATOR",
                start_time=(
                    first_start
                    + timedelta(minutes=15)
                ),
            )

    def test_stop_rejects_time_after_execution_end(self):
        execution = self.get_running_execution()
        event_start = (
            execution.start_time
            + timedelta(hours=1)
        )
        event = self.downtime_service.start_downtime(
            execution.id,
            "WAIT_MATERIAL",
            start_time=event_start,
        )
        execution.end_time = (
            event_start
            + timedelta(minutes=20)
        )
        execution.status = "STOPPED"
        self.session.flush()

        with self.assertRaisesRegex(
            ValueError,
            "cannot be after Execution End Time",
        ):
            self.downtime_service.stop_downtime(
                event.id,
                end_time=(
                    event_start
                    + timedelta(minutes=30)
                ),
            )
