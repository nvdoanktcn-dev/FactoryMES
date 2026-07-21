import unittest
from datetime import datetime, timedelta

from src.execution import (
    ExecutionTask,
    InvalidExecutionTaskError,
    InvalidProductionQuantityError,
    TaskStatus,
)
from src.scheduler.models import MachineBooking


class TestExecutionModels(unittest.TestCase):

    def setUp(self) -> None:
        self.start_time = datetime(
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
            start_time=self.start_time,
            end_time=self.start_time + timedelta(minutes=60),
            quantity=100,
        )

    def test_create_task_with_default_status(self) -> None:
        task = ExecutionTask(
            booking=self.booking
        )

        self.assertEqual(
            task.status,
            TaskStatus.WAITING,
        )

    def test_task_exposes_booking_properties(self) -> None:
        task = ExecutionTask(
            booking=self.booking
        )

        self.assertEqual(
            task.work_order_code,
            "WO-001",
        )
        self.assertEqual(
            task.product_code,
            "P-001",
        )
        self.assertEqual(
            task.machine_code,
            "BL01",
        )
        self.assertEqual(
            task.op_code,
            "OP10",
        )
        self.assertEqual(
            task.sequence,
            10,
        )

    def test_produced_quantity(self) -> None:
        task = ExecutionTask(
            booking=self.booking,
            ok_qty=90,
            ng_qty=5,
        )

        self.assertEqual(
            task.produced_quantity,
            95,
        )

    def test_remaining_quantity(self) -> None:
        task = ExecutionTask(
            booking=self.booking,
            ok_qty=80,
            ng_qty=10,
        )

        self.assertEqual(
            task.remaining_quantity,
            10,
        )

    def test_remaining_quantity_never_negative(self) -> None:
        task = ExecutionTask(
            booking=self.booking,
            ok_qty=100,
            ng_qty=0,
        )

        self.assertEqual(
            task.remaining_quantity,
            0,
        )

    def test_terminal_status(self) -> None:
        finished_task = ExecutionTask(
            booking=self.booking,
            status=TaskStatus.FINISHED,
            started_at=self.start_time,
            finished_at=(
                self.start_time
                + timedelta(minutes=60)
            ),
        )

        cancelled_task = ExecutionTask(
            booking=self.booking,
            status=TaskStatus.CANCELLED,
        )

        self.assertTrue(
            finished_task.is_terminal
        )
        self.assertTrue(
            cancelled_task.is_terminal
        )

    def test_running_status_is_not_terminal(self) -> None:
        task = ExecutionTask(
            booking=self.booking,
            status=TaskStatus.RUNNING,
        )

        self.assertFalse(
            task.is_terminal
        )

    def test_actual_runtime_excludes_downtime(self) -> None:
        task = ExecutionTask(
            booking=self.booking,
            status=TaskStatus.FINISHED,
            started_at=self.start_time,
            finished_at=(
                self.start_time
                + timedelta(minutes=90)
            ),
            downtime_minutes=15.0,
        )

        self.assertEqual(
            task.actual_runtime_minutes,
            75.0,
        )

    def test_invalid_booking_raises_error(self) -> None:
        with self.assertRaises(
            InvalidExecutionTaskError
        ):
            ExecutionTask(
                booking=None
            )

    def test_negative_ok_quantity_raises_error(self) -> None:
        with self.assertRaises(
            InvalidProductionQuantityError
        ):
            ExecutionTask(
                booking=self.booking,
                ok_qty=-1,
            )

    def test_negative_ng_quantity_raises_error(self) -> None:
        with self.assertRaises(
            InvalidProductionQuantityError
        ):
            ExecutionTask(
                booking=self.booking,
                ng_qty=-1,
            )

    def test_negative_downtime_raises_error(self) -> None:
        with self.assertRaises(
            InvalidExecutionTaskError
        ):
            ExecutionTask(
                booking=self.booking,
                downtime_minutes=-1,
            )

    def test_finish_before_start_raises_error(self) -> None:
        with self.assertRaises(
            InvalidExecutionTaskError
        ):
            ExecutionTask(
                booking=self.booking,
                started_at=self.start_time,
                finished_at=(
                    self.start_time
                    - timedelta(minutes=1)
                ),
            )

    def test_finished_task_requires_finished_at(self) -> None:
        with self.assertRaises(
            InvalidExecutionTaskError
        ):
            ExecutionTask(
                booking=self.booking,
                status=TaskStatus.FINISHED,
                started_at=self.start_time,
            )

    def test_validate_quantity_success(self) -> None:
        task = ExecutionTask(
            booking=self.booking
        )

        task.validate_quantity(
            ok_qty=90,
            ng_qty=10,
        )

    def test_validate_quantity_over_plan_raises_error(
        self,
    ) -> None:
        task = ExecutionTask(
            booking=self.booking
        )

        with self.assertRaises(
            InvalidProductionQuantityError
        ):
            task.validate_quantity(
                ok_qty=100,
                ng_qty=1,
            )

    def test_task_is_completed(self) -> None:
        task = ExecutionTask(
            booking=self.booking,
            ok_qty=95,
            ng_qty=5,
        )

        self.assertTrue(
            task.is_completed,
            )
    

    def test_partial_task_is_not_completed(self) -> None:
        task = ExecutionTask(
            booking=self.booking,
            ok_qty=80,
            ng_qty=5,
        )

        self.assertFalse(
            task.is_completed,
        )


if __name__ == "__main__":
    unittest.main()