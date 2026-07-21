import unittest
from datetime import datetime, timedelta

from src.execution import (
    ExecutionEngine,
    ExecutionTask,
    InvalidExecutionTaskError,
    InvalidProductionQuantityError,
    InvalidTaskTransitionError,
    TaskAlreadyFinishedError,
    TaskStatus,
)
from src.scheduler.models import MachineBooking


class TestExecutionEngine(unittest.TestCase):

    def setUp(self) -> None:
        start_time = datetime(
            2026,
            7,
            20,
            8,
            0,
        )

        self.booking = MachineBooking(
            work_order_code="WO-001",
            product_code="P-001",
            machine_group="CNC",
            machine_code="BL01",
            op_code="OP10",
            sequence=10,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=60),
            quantity=100,
        )

        self.task = ExecutionTask(
            booking=self.booking,
        )

        self.engine = ExecutionEngine()

    def _start_task(self) -> None:
        self.engine.ready(self.task)
        self.engine.start(self.task)

    def test_waiting_to_ready(self) -> None:
        self.engine.ready(self.task)

        self.assertEqual(
            self.task.status,
            TaskStatus.READY,
        )

    def test_ready_to_running(self) -> None:
        self.engine.ready(self.task)
        self.engine.start(self.task)

        self.assertEqual(
            self.task.status,
            TaskStatus.RUNNING,
        )
        self.assertIsNotNone(
            self.task.started_at,
        )

    def test_running_to_paused(self) -> None:
        self._start_task()

        self.engine.pause(self.task)

        self.assertEqual(
            self.task.status,
            TaskStatus.PAUSED,
        )

    def test_paused_to_running(self) -> None:
        self._start_task()
        self.engine.pause(self.task)

        self.engine.resume(self.task)

        self.assertEqual(
            self.task.status,
            TaskStatus.RUNNING,
        )

    def test_resume_does_not_replace_started_at(
        self,
    ) -> None:
        self._start_task()
        original_started_at = self.task.started_at

        self.engine.pause(self.task)
        self.engine.resume(self.task)

        self.assertEqual(
            self.task.started_at,
            original_started_at,
        )

    def test_running_to_finished(self) -> None:
        self._start_task()

        self.engine.finish(self.task)

        self.assertEqual(
            self.task.status,
            TaskStatus.FINISHED,
        )
        self.assertIsNotNone(
            self.task.finished_at,
        )

    def test_waiting_to_finished_is_invalid(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidTaskTransitionError,
        ):
            self.engine.finish(self.task)

    def test_ready_to_finished_is_invalid(
        self,
    ) -> None:
        self.engine.ready(self.task)

        with self.assertRaises(
            InvalidTaskTransitionError,
        ):
            self.engine.finish(self.task)

    def test_waiting_to_paused_is_invalid(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidTaskTransitionError,
        ):
            self.engine.pause(self.task)

    def test_finished_task_cannot_restart(
        self,
    ) -> None:
        self._start_task()
        self.engine.finish(self.task)

        with self.assertRaises(
            TaskAlreadyFinishedError,
        ):
            self.engine.start(self.task)

    def test_waiting_task_can_be_cancelled(
        self,
    ) -> None:
        self.engine.cancel(self.task)

        self.assertEqual(
            self.task.status,
            TaskStatus.CANCELLED,
        )

    def test_ready_task_can_be_cancelled(
        self,
    ) -> None:
        self.engine.ready(self.task)

        self.engine.cancel(self.task)

        self.assertEqual(
            self.task.status,
            TaskStatus.CANCELLED,
        )

    def test_running_task_can_be_cancelled(
        self,
    ) -> None:
        self._start_task()

        self.engine.cancel(self.task)

        self.assertEqual(
            self.task.status,
            TaskStatus.CANCELLED,
        )

    def test_paused_task_can_be_cancelled(
        self,
    ) -> None:
        self._start_task()
        self.engine.pause(self.task)

        self.engine.cancel(self.task)

        self.assertEqual(
            self.task.status,
            TaskStatus.CANCELLED,
        )

    def test_cancelled_task_cannot_be_started(
        self,
    ) -> None:
        self.engine.cancel(self.task)

        with self.assertRaises(
            InvalidTaskTransitionError,
        ):
            self.engine.start(self.task)

    def test_record_ok_quantity(self) -> None:
        self._start_task()

        self.engine.record_production(
            self.task,
            ok_qty=80,
        )

        self.assertEqual(
            self.task.ok_qty,
            80,
        )
        self.assertEqual(
            self.task.ng_qty,
            0,
        )

    def test_record_ng_quantity(self) -> None:
        self._start_task()

        self.engine.record_production(
            self.task,
            ok_qty=80,
            ng_qty=10,
        )

        self.assertEqual(
            self.task.ok_qty,
            80,
        )
        self.assertEqual(
            self.task.ng_qty,
            10,
        )

    def test_record_production_accumulates(
        self,
    ) -> None:
        self._start_task()

        self.engine.record_production(
            self.task,
            ok_qty=40,
            ng_qty=5,
        )
        self.engine.record_production(
            self.task,
            ok_qty=30,
            ng_qty=5,
        )

        self.assertEqual(
            self.task.ok_qty,
            70,
        )
        self.assertEqual(
            self.task.ng_qty,
            10,
        )
        self.assertEqual(
            self.task.produced_quantity,
            80,
        )

    def test_record_production_over_plan_raises_error(
        self,
    ) -> None:
        self._start_task()

        self.engine.record_production(
            self.task,
            ok_qty=90,
            ng_qty=5,
        )

        with self.assertRaises(
            InvalidProductionQuantityError,
        ):
            self.engine.record_production(
                self.task,
                ok_qty=6,
            )

    def test_negative_ok_quantity_raises_error(
        self,
    ) -> None:
        self._start_task()

        with self.assertRaises(
            InvalidProductionQuantityError,
        ):
            self.engine.record_production(
                self.task,
                ok_qty=-1,
            )

    def test_negative_ng_quantity_raises_error(
        self,
    ) -> None:
        self._start_task()

        with self.assertRaises(
            InvalidProductionQuantityError,
        ):
            self.engine.record_production(
                self.task,
                ok_qty=0,
                ng_qty=-1,
            )

    def test_waiting_task_cannot_record_production(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidTaskTransitionError,
        ):
            self.engine.record_production(
                self.task,
                ok_qty=10,
            )

    def test_ready_task_cannot_record_production(
        self,
    ) -> None:
        self.engine.ready(self.task)

        with self.assertRaises(
            InvalidTaskTransitionError,
        ):
            self.engine.record_production(
                self.task,
                ok_qty=10,
            )

    def test_paused_task_cannot_record_production(
        self,
    ) -> None:
        self._start_task()
        self.engine.pause(self.task)

        with self.assertRaises(
            InvalidTaskTransitionError,
        ):
            self.engine.record_production(
                self.task,
                ok_qty=10,
            )

    def test_cancelled_task_cannot_record_production(
        self,
    ) -> None:
        self.engine.cancel(self.task)

        with self.assertRaises(
            InvalidTaskTransitionError,
        ):
            self.engine.record_production(
                self.task,
                ok_qty=10,
            )

    def test_finished_task_cannot_record_production(
        self,
    ) -> None:
        self._start_task()

        self.engine.record_production(
            self.task,
            ok_qty=100,
        )

        with self.assertRaises(
            TaskAlreadyFinishedError,
        ):
            self.engine.record_production(
                self.task,
                ok_qty=0,
            )

    def test_full_quantity_auto_finishes_task(
        self,
    ) -> None:
        self._start_task()

        self.engine.record_production(
            self.task,
            ok_qty=95,
            ng_qty=5,
        )

        self.assertEqual(
            self.task.status,
            TaskStatus.FINISHED,
        )

    def test_auto_finish_sets_finished_at(
        self,
    ) -> None:
        self._start_task()

        self.engine.record_production(
            self.task,
            ok_qty=100,
        )

        self.assertIsNotNone(
            self.task.finished_at,
        )

    def test_partial_quantity_keeps_task_running(
        self,
    ) -> None:
        self._start_task()

        self.engine.record_production(
            self.task,
            ok_qty=80,
            ng_qty=5,
        )

        self.assertEqual(
            self.task.status,
            TaskStatus.RUNNING,
        )
        self.assertIsNone(
            self.task.finished_at,
        )

    def test_invalid_task_object_raises_error(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidExecutionTaskError,
        ):
            self.engine.ready(None)


if __name__ == "__main__":
    unittest.main()