from __future__ import annotations

from datetime import datetime

from src.services.production_execution_service import (
    ProductionExecutionService,
)
from tests.base.database_test_case import DatabaseTestCase
from tests.factories.production_assignment_factory import (
    ProductionAssignmentFactory,
)
from src.framework.exception import NotFoundError


class TestProductionExecutionQuantityAggregation(
    DatabaseTestCase
):
    def setUp(self):
        super().setUp()

        self.service = ProductionExecutionService(
            session=self.session
        )

        self.assignment = (
            ProductionAssignmentFactory.create_in_progress(
                self.session
            )
        )

        self.session.flush()

    def _create_stopped_execution(
        self,
        *,
        start_time,
        end_time,
        ok_qty,
        ng_qty,
        processing_ng_qty,
        blank_ng_qty,
        downtime_minutes,
        complete=False,
    ):
        execution = self.service.start_execution(
            self.assignment.id,
            start_time=start_time,
        )

        return self.service.stop_execution(
            execution.id,
            ok_qty=ok_qty,
            ng_qty=ng_qty,
            processing_ng_qty=processing_ng_qty,
            blank_ng_qty=blank_ng_qty,
            downtime_minutes=downtime_minutes,
            end_time=end_time,
            complete=complete,
        )

    def test_aggregate_assignment_quantities(
        self,
    ):
        first = self._create_stopped_execution(
            start_time=datetime(
                2026, 8, 20, 8, 0
            ),
            end_time=datetime(
                2026, 8, 20, 9, 0
            ),
            ok_qty=40,
            ng_qty=5,
            processing_ng_qty=3,
            blank_ng_qty=2,
            downtime_minutes=10,
            complete=False,
        )

        second = self._create_stopped_execution(
            start_time=datetime(
                2026, 8, 20, 9, 0
            ),
            end_time=datetime(
                2026, 8, 20, 10, 30
            ),
            ok_qty=50,
            ng_qty=5,
            processing_ng_qty=4,
            blank_ng_qty=1,
            downtime_minutes=15,
            complete=True,
        )

        cancelled = self.service.start_execution(
            self.assignment.id,
            start_time=datetime(
                2026, 8, 20, 10, 30
            ),
        )

        self.service.stop_execution(
            cancelled.id,
            ok_qty=999,
            ng_qty=1,
            processing_ng_qty=1,
            blank_ng_qty=0,
            downtime_minutes=0,
            end_time=datetime(
                2026, 8, 20, 11, 0
            ),
            complete=False,
        )

        self.service.cancel_execution(
            cancelled.id
        )

        running = self.service.start_execution(
            self.assignment.id,
            start_time=datetime(
                2026, 8, 20, 11, 0
            ),
        )

        self.session.flush()

        result = (
            self.service
            .aggregate_assignment_quantities(
                self.assignment.id
            )
        )

        self.assertEqual(
            result["assignment_id"],
            self.assignment.id,
        )
        self.assertEqual(
            result["execution_count"],
            2,
        )

        self.assertEqual(
            result["ok_qty"],
            90,
        )
        self.assertEqual(
            result["ng_qty"],
            10,
        )
        self.assertEqual(
            result["processing_ng_qty"],
            7,
        )
        self.assertEqual(
            result["blank_ng_qty"],
            3,
        )

        # First:
        # 60 elapsed - 10 downtime = 50 runtime.
        #
        # Second:
        # 90 elapsed - 15 downtime = 75 runtime.
        self.assertAlmostEqual(
            result["runtime_minutes"],
            125.0,
        )
        self.assertAlmostEqual(
            result["downtime_minutes"],
            25.0,
        )

        self.assertEqual(
            first.status,
            "STOPPED",
        )
        self.assertEqual(
            second.status,
            "COMPLETED",
        )
        self.assertEqual(
            cancelled.status,
            "CANCELLED",
        )
        self.assertEqual(
            running.status,
            "RUNNING",
        )

    def test_aggregate_empty_assignment_returns_zero(
        self,
    ):
        result = (
            self.service
            .aggregate_assignment_quantities(
                self.assignment.id
            )
        )

        self.assertEqual(
            result,
            {
                "assignment_id": self.assignment.id,
                "execution_count": 0,
                "ok_qty": 0,
                "ng_qty": 0,
                "processing_ng_qty": 0,
                "blank_ng_qty": 0,
                "runtime_minutes": 0,
                "downtime_minutes": 0,
            },
        )

    def test_aggregate_rejects_unknown_assignment(
        self,
    ):
        with self.assertRaisesRegex(
            NotFoundError,
            "Production Assignment not found",
        ):
            self.service.aggregate_assignment_quantities(
                999999
            )