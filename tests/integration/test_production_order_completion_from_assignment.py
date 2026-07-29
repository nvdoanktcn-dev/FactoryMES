from __future__ import annotations

from datetime import datetime

from src.framework.exception import NotFoundError
from src.services.production_assignment_service import (
    ProductionAssignmentService,
)
from src.services.production_execution_service import (
    ProductionExecutionService,
)
from src.services.production_order_service import (
    ProductionOrderService,
)
from tests.base.database_test_case import DatabaseTestCase
from tests.factories.production_assignment_factory import (
    ProductionAssignmentFactory,
)


class TestProductionOrderCompletionFromAssignment(
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
        self.order_service = (
            ProductionOrderService(
                session=self.session
            )
        )

        self.assignment = (
            ProductionAssignmentFactory
            .create_in_progress(
                self.session
            )
        )

        self.production_order = (
            self.session
            .get(
                type(
                    ProductionAssignmentFactory
                    .get_production_order(
                        self.session
                    )
                ),
                self.assignment.production_order_id,
            )
        )

        self.session.flush()

    def _stop_execution(
        self,
        *,
        start_time,
        end_time,
        ok_qty,
        ng_qty,
        processing_ng_qty,
        blank_ng_qty,
        complete=False,
    ):
        execution = (
            self.execution_service
            .start_execution(
                self.assignment.id,
                start_time=start_time,
            )
        )

        return (
            self.execution_service
            .stop_execution(
                execution.id,
                ok_qty=ok_qty,
                ng_qty=ng_qty,
                processing_ng_qty=(
                    processing_ng_qty
                ),
                blank_ng_qty=blank_ng_qty,
                downtime_minutes=0,
                end_time=end_time,
                complete=complete,
            )
        )

    def test_complete_order_from_multiple_executions(
        self,
    ):
        self._stop_execution(
            start_time=datetime(
                2026, 8, 21, 8, 0
            ),
            end_time=datetime(
                2026, 8, 21, 9, 0
            ),
            ok_qty=40,
            ng_qty=5,
            processing_ng_qty=3,
            blank_ng_qty=2,
        )

        self._stop_execution(
            start_time=datetime(
                2026, 8, 21, 9, 0
            ),
            end_time=datetime(
                2026, 8, 21, 10, 0
            ),
            ok_qty=50,
            ng_qty=5,
            processing_ng_qty=4,
            blank_ng_qty=1,
            complete=True,
        )

        cancelled = self._stop_execution(
            start_time=datetime(
                2026, 8, 21, 10, 0
            ),
            end_time=datetime(
                2026, 8, 21, 10, 30
            ),
            ok_qty=999,
            ng_qty=1,
            processing_ng_qty=1,
            blank_ng_qty=0,
        )

        self.execution_service.cancel_execution(
            cancelled.id
        )

        self.assignment_service.complete(
            self.assignment.id,
            actual_finish=datetime(
                2026, 8, 21, 10, 30
            ),
        )

        result = (
            self.order_service
            .complete_from_assignment(
                self.assignment.id,
                actual_finish=datetime(
                    2026, 8, 21, 10, 30
                ),
            )
        )

        self.session.flush()
        self.session.expire_all()

        persisted = (
            self.order_service
            .get_production_order(
                result.work_order_no,
                result.operation_no,
            )
        )

        self.assertEqual(
            persisted.status,
            "COMPLETED",
        )
        self.assertEqual(
            persisted.completed_qty,
            90,
        )
        self.assertEqual(
            persisted.ng_qty,
            10,
        )
        self.assertEqual(
            persisted.actual_finish,
            datetime(
                2026, 8, 21, 10, 30
            ),
        )

    def test_rejects_incomplete_assignment(
        self,
    ):
        self._stop_execution(
            start_time=datetime(
                2026, 8, 22, 8, 0
            ),
            end_time=datetime(
                2026, 8, 22, 9, 0
            ),
            ok_qty=90,
            ng_qty=10,
            processing_ng_qty=5,
            blank_ng_qty=5,
        )

        with self.assertRaisesRegex(
            ValueError,
            "Assignment must be COMPLETED",
        ):
            self.order_service.complete_from_assignment(
                self.assignment.id
            )

        self.assertNotEqual(
            self.production_order.status,
            "COMPLETED",
        )

    def test_rejects_running_execution(
        self,
    ):
        self.execution_service.start_execution(
            self.assignment.id,
            start_time=datetime(
                2026, 8, 23, 8, 0
            ),
        )

        # Arrange an intentionally inconsistent persisted state so this
        # test isolates ProductionOrderService validation. The normal
        # ProductionAssignmentService.complete() workflow correctly rejects
        # completion while an execution is RUNNING.
        self.assignment.status = "COMPLETED"
        self.assignment.actual_finish = datetime(
            2026, 8, 23, 9, 0
        )
        self.session.flush()

        with self.assertRaisesRegex(
            ValueError,
            "RUNNING execution",
        ):
            self.order_service.complete_from_assignment(
                self.assignment.id
            )

        self.assertNotEqual(
            self.production_order.status,
            "COMPLETED",
        )

    def test_rejects_quantity_above_plan(
        self,
    ):
        self._stop_execution(
            start_time=datetime(
                2026, 8, 24, 8, 0
            ),
            end_time=datetime(
                2026, 8, 24, 9, 0
            ),
            ok_qty=100,
            ng_qty=1,
            processing_ng_qty=1,
            blank_ng_qty=0,
        )

        self.assignment_service.complete(
            self.assignment.id,
            actual_finish=datetime(
                2026, 8, 24, 9, 0
            ),
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                "Execution OK Qty \\+ NG Qty "
                "cannot be greater"
            ),
        ):
            self.order_service.complete_from_assignment(
                self.assignment.id
            )

        self.session.refresh(
            self.production_order
        )

        self.assertNotEqual(
            self.production_order.status,
            "COMPLETED",
        )
        self.assertEqual(
            self.production_order.completed_qty,
            0,
        )
        self.assertEqual(
            self.production_order.ng_qty,
            0,
        )

    def test_rejects_assignment_without_results(
        self,
    ):
        # Arrange a COMPLETED assignment without finalized execution
        # results to test ProductionOrderService in isolation. The normal
        # assignment workflow prevents this invalid state.
        self.assignment.status = "COMPLETED"
        self.assignment.actual_finish = datetime(
            2026, 8, 25, 9, 0
        )
        self.session.flush()

        with self.assertRaisesRegex(
            ValueError,
            "at least one STOPPED or COMPLETED",
        ):
            self.order_service.complete_from_assignment(
                self.assignment.id
            )

    def test_rejects_unknown_assignment(
        self,
    ):
        with self.assertRaisesRegex(
            NotFoundError,
            "Production Assignment not found",
        ):
            self.order_service.complete_from_assignment(
                999999
            )