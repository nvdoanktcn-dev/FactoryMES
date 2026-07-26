from tests.base_db_test import DatabaseTestCase

from src.framework.exception import NotFoundError
from src.models.production_assignment import ProductionAssignment
from src.services.production_execution_service import (
    ProductionExecutionService,
)


class TestProductionExecutionService(DatabaseTestCase):

    def setUp(self):
        super().setUp()
        self.service = ProductionExecutionService(session=self.session)

    def get_available_assignment(self):
        assignments = (
            self.session.query(ProductionAssignment)
            .filter(ProductionAssignment.status == "IN_PROGRESS")
            .order_by(ProductionAssignment.id.asc())
            .all()
        )

        for assignment in assignments:
            running = (
                self.service.repository
                .get_running_by_assignment_id(assignment.id)
            )
            if running is None:
                return assignment

        self.skipTest(
            "Không có Assignment IN_PROGRESS phù hợp. "
            "Hãy release và start một Assignment trước."
        )

    def get_non_in_progress_assignment(self):
        assignment = (
            self.session.query(ProductionAssignment)
            .filter(ProductionAssignment.status != "IN_PROGRESS")
            .order_by(ProductionAssignment.id.asc())
            .first()
        )

        if assignment is None:
            self.skipTest(
                "Không có Assignment ngoài trạng thái IN_PROGRESS."
            )

        return assignment

    def start_execution(self):
        assignment = self.get_available_assignment()
        execution = self.service.start_execution(
            assignment.id,
            start_time="2026-07-20 08:00",
            remark="Execution service test",
        )
        self.session.flush()
        return assignment, execution

    def test_start_execution_success(self):
        assignment, execution = self.start_execution()

        self.assertIsNotNone(execution.id)
        self.assertEqual(execution.assignment_id, assignment.id)
        self.assertEqual(execution.status, "RUNNING")
        self.assertEqual(execution.remark, "Execution service test")

    def test_start_execution_assignment_not_found(self):
        with self.assertRaises(NotFoundError):
            self.service.start_execution(
                999999999,
                start_time="2026-07-20 08:00",
            )

    def test_start_execution_invalid_assignment_id(self):
        with self.assertRaises(NotFoundError):
            self.service.start_execution(
                "invalid-id",
                start_time="2026-07-20 08:00",
            )

    def test_start_execution_assignment_not_in_progress(self):
        assignment = self.get_non_in_progress_assignment()

        with self.assertRaisesRegex(ValueError, "must be IN_PROGRESS"):
            self.service.start_execution(
                assignment.id,
                start_time="2026-07-20 08:00",
            )

    def test_start_execution_duplicate_running(self):
        assignment, _ = self.start_execution()

        with self.assertRaisesRegex(
            ValueError,
            "RUNNING execution already exists",
        ):
            self.service.start_execution(
                assignment.id,
                start_time="2026-07-20 09:00",
            )

    def test_start_execution_invalid_datetime(self):
        assignment = self.get_available_assignment()

        with self.assertRaisesRegex(ValueError, "Invalid datetime"):
            self.service.start_execution(
                assignment.id,
                start_time="not-a-date",
            )

    def test_start_execution_cleans_remark(self):
        assignment = self.get_available_assignment()
        execution = self.service.start_execution(
            assignment.id,
            start_time="2026-07-20 08:00",
            remark="   test remark   ",
        )

        self.assertEqual(execution.remark, "test remark")

    def test_start_and_stop_execution_completed(self):
        _, execution = self.start_execution()

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
        self.assertEqual(execution.runtime_minutes, 210)
        self.assertEqual(execution.status, "COMPLETED")

    def test_stop_execution_sets_stopped_by_default(self):
        _, execution = self.start_execution()

        execution = self.service.stop_execution(
            execution.id,
            end_time="2026-07-20 09:00",
        )

        self.assertEqual(execution.status, "STOPPED")
        self.assertEqual(execution.runtime_minutes, 60)

    def test_stop_execution_not_found(self):
        with self.assertRaises(NotFoundError):
            self.service.stop_execution(
                999999999,
                end_time="2026-07-20 09:00",
            )

    def test_stop_execution_only_running(self):
        _, execution = self.start_execution()
        self.service.stop_execution(
            execution.id,
            end_time="2026-07-20 09:00",
        )

        with self.assertRaisesRegex(
            ValueError,
            "Only RUNNING execution",
        ):
            self.service.stop_execution(
                execution.id,
                end_time="2026-07-20 10:00",
            )

    def test_stop_execution_end_must_be_after_start(self):
        _, execution = self.start_execution()

        with self.assertRaisesRegex(ValueError, "after Start Time"):
            self.service.stop_execution(
                execution.id,
                end_time="2026-07-20 08:00",
            )

    def test_stop_execution_negative_ok_qty(self):
        _, execution = self.start_execution()

        with self.assertRaisesRegex(ValueError, "OK Qty cannot be negative"):
            self.service.stop_execution(
                execution.id,
                ok_qty=-1,
                end_time="2026-07-20 09:00",
            )

    def test_stop_execution_negative_ng_qty(self):
        _, execution = self.start_execution()

        with self.assertRaisesRegex(ValueError, "NG Qty cannot be negative"):
            self.service.stop_execution(
                execution.id,
                ng_qty=-1,
                end_time="2026-07-20 09:00",
            )

    def test_stop_execution_negative_processing_ng_qty(self):
        _, execution = self.start_execution()

        with self.assertRaisesRegex(
            ValueError,
            "Processing NG Qty cannot be negative",
        ):
            self.service.stop_execution(
                execution.id,
                processing_ng_qty=-1,
                end_time="2026-07-20 09:00",
            )

    def test_stop_execution_negative_blank_ng_qty(self):
        _, execution = self.start_execution()

        with self.assertRaisesRegex(
            ValueError,
            "Blank NG Qty cannot be negative",
        ):
            self.service.stop_execution(
                execution.id,
                blank_ng_qty=-1,
                end_time="2026-07-20 09:00",
            )

    def test_stop_execution_ng_breakdown_must_match_total(self):
        _, execution = self.start_execution()

        with self.assertRaisesRegex(ValueError, "must equal NG Qty"):
            self.service.stop_execution(
                execution.id,
                ng_qty=5,
                processing_ng_qty=3,
                blank_ng_qty=1,
                end_time="2026-07-20 09:00",
            )

        self.assertEqual(execution.status, "RUNNING")
        self.assertIsNone(execution.end_time)

    def test_stop_execution_negative_downtime(self):
        _, execution = self.start_execution()

        with self.assertRaisesRegex(
            ValueError,
            "Downtime Minutes cannot be negative",
        ):
            self.service.stop_execution(
                execution.id,
                downtime_minutes=-1,
                end_time="2026-07-20 09:00",
            )

    def test_stop_execution_downtime_cannot_exceed_elapsed(self):
        _, execution = self.start_execution()

        with self.assertRaisesRegex(
            ValueError,
            "cannot exceed elapsed time",
        ):
            self.service.stop_execution(
                execution.id,
                downtime_minutes=61,
                end_time="2026-07-20 09:00",
            )

        self.assertEqual(execution.status, "RUNNING")
        self.assertIsNone(execution.end_time)

    def test_stop_execution_downtime_can_equal_elapsed(self):
        _, execution = self.start_execution()

        execution = self.service.stop_execution(
            execution.id,
            downtime_minutes=60,
            end_time="2026-07-20 09:00",
        )

        self.assertEqual(execution.runtime_minutes, 0)
        self.assertEqual(execution.status, "STOPPED")

    def test_stop_execution_updates_remark(self):
        _, execution = self.start_execution()

        execution = self.service.stop_execution(
            execution.id,
            end_time="2026-07-20 09:00",
            remark="   finished test   ",
        )

        self.assertEqual(execution.remark, "finished test")

    def test_cancel_execution_success(self):
        _, execution = self.start_execution()

        execution = self.service.cancel_execution(execution.id)

        self.assertEqual(execution.status, "CANCELLED")

    def test_cancel_completed_execution_fails(self):
        _, execution = self.start_execution()
        execution = self.service.stop_execution(
            execution.id,
            end_time="2026-07-20 09:00",
            complete=True,
        )

        with self.assertRaisesRegex(
            ValueError,
            "COMPLETED execution cannot be cancelled",
        ):
            self.service.cancel_execution(execution.id)

    def test_cancel_execution_twice_fails(self):
        _, execution = self.start_execution()
        self.service.cancel_execution(execution.id)

        with self.assertRaisesRegex(ValueError, "already CANCELLED"):
            self.service.cancel_execution(execution.id)

    def test_start_execution_rejects_overlap_with_previous_run(self):
        assignment, execution = self.start_execution()
        self.service.stop_execution(
            execution.id,
            end_time="2026-07-20 10:00",
        )

        with self.assertRaisesRegex(
            ValueError,
            "Start Time overlaps",
        ):
            self.service.start_execution(
                assignment.id,
                start_time="2026-07-20 09:00",
            )

    def test_stop_execution_rejects_fractional_quantity(self):
        _, execution = self.start_execution()

        with self.assertRaisesRegex(
            ValueError,
            "OK Qty must be a whole number",
        ):
            self.service.stop_execution(
                execution.id,
                ok_qty=1.5,
                end_time="2026-07-20 09:00",
            )

    def test_stop_execution_rejects_non_finite_downtime(self):
        _, execution = self.start_execution()

        with self.assertRaisesRegex(
            ValueError,
            "Downtime Minutes must be a finite number",
        ):
            self.service.stop_execution(
                execution.id,
                downtime_minutes=float("nan"),
                end_time="2026-07-20 09:00",
            )
