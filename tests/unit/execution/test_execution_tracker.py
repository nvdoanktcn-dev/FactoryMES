import unittest
from datetime import datetime, timedelta

from src.execution import (
    DuplicateExecutionTaskError,
    ExecutionEngine,
    ExecutionTask,
    ExecutionTaskNotFoundError,
    ExecutionTracker,
    InvalidExecutionTaskError,
    TaskStatus,
)
from src.scheduler.models import MachineBooking


class TestExecutionTracker(unittest.TestCase):

    def setUp(self) -> None:
        self.start_time = datetime(
            2026,
            7,
            20,
            8,
            0,
        )

        self.tracker = ExecutionTracker()
        self.engine = ExecutionEngine()

        self.task_1 = self._create_task(
            machine_code="BL01",
            work_order_code="WO-001",
            product_code="P-001",
            op_code="OP10",
            quantity=100,
        )

        self.task_2 = self._create_task(
            machine_code="BL02",
            work_order_code="WO-001",
            product_code="P-001",
            op_code="OP20",
            quantity=80,
        )

        self.task_3 = self._create_task(
            machine_code="BR01",
            work_order_code="WO-002",
            product_code="P-002",
            op_code="OP10",
            quantity=50,
        )

    def _create_task(
        self,
        machine_code: str,
        work_order_code: str,
        product_code: str,
        op_code: str,
        quantity: int,
    ) -> ExecutionTask:
        booking = MachineBooking(
            work_order_code=work_order_code,
            product_code=product_code,
            machine_group=(
                "ROBOT"
                if machine_code.startswith("BR")
                else "CNC"
            ),
            machine_code=machine_code,
            op_code=op_code,
            sequence=10,
            start_time=self.start_time,
            end_time=(
                self.start_time
                + timedelta(minutes=60)
            ),
            quantity=quantity,
        )

        return ExecutionTask(
            booking=booking,
        )

    def test_add_task(self) -> None:
        self.tracker.add(self.task_1)

        self.assertEqual(
            self.tracker.total_tasks,
            1,
        )

    def test_get_task(self) -> None:
        self.tracker.add(self.task_1)

        result = self.tracker.get(
            machine_code="BL01",
            work_order_code="WO-001",
            op_code="OP10",
        )

        self.assertIs(
            result,
            self.task_1,
        )

    def test_get_is_case_insensitive(self) -> None:
        self.tracker.add(self.task_1)

        result = self.tracker.get(
            machine_code="bl01",
            work_order_code="wo-001",
            op_code="op10",
        )

        self.assertIs(
            result,
            self.task_1,
        )

    def test_duplicate_task_raises_error(self) -> None:
        self.tracker.add(self.task_1)

        with self.assertRaises(
            DuplicateExecutionTaskError
        ):
            self.tracker.add(self.task_1)

    def test_missing_task_raises_error(self) -> None:
        with self.assertRaises(
            ExecutionTaskNotFoundError
        ):
            self.tracker.get(
                machine_code="BL99",
                work_order_code="WO-999",
                op_code="OP99",
            )

    def test_remove_task(self) -> None:
        self.tracker.add(self.task_1)

        removed = self.tracker.remove(
            machine_code="BL01",
            work_order_code="WO-001",
            op_code="OP10",
        )

        self.assertIs(
            removed,
            self.task_1,
        )
        self.assertEqual(
            len(self.tracker),
            0,
        )

    def test_find_by_machine(self) -> None:
        self.tracker.add(self.task_1)
        self.tracker.add(self.task_2)

        result = self.tracker.find_by_machine(
            "BL01"
        )

        self.assertEqual(
            result,
            (self.task_1,),
        )

    def test_find_by_work_order(self) -> None:
        self.tracker.add(self.task_1)
        self.tracker.add(self.task_2)
        self.tracker.add(self.task_3)

        result = self.tracker.find_by_work_order(
            "WO-001"
        )

        self.assertEqual(
            len(result),
            2,
        )

    def test_find_by_product(self) -> None:
        self.tracker.add(self.task_1)
        self.tracker.add(self.task_2)
        self.tracker.add(self.task_3)

        result = self.tracker.find_by_product(
            "P-001"
        )

        self.assertEqual(
            len(result),
            2,
        )

    def test_find_by_status(self) -> None:
        self.tracker.add(self.task_1)
        self.tracker.add(self.task_2)

        self.engine.ready(self.task_1)

        result = self.tracker.find_by_status(
            TaskStatus.READY
        )

        self.assertEqual(
            result,
            (self.task_1,),
        )

    def test_total_planned_quantity(self) -> None:
        self.tracker.add(self.task_1)
        self.tracker.add(self.task_2)

        self.assertEqual(
            self.tracker.total_planned_quantity,
            180,
        )

    def test_total_ok_and_ng_quantity(self) -> None:
        self.tracker.add(self.task_1)
        self.tracker.add(self.task_2)

        self.engine.ready(self.task_1)
        self.engine.start(self.task_1)
        self.engine.record_production(
            self.task_1,
            ok_qty=80,
            ng_qty=10,
        )

        self.engine.ready(self.task_2)
        self.engine.start(self.task_2)
        self.engine.record_production(
            self.task_2,
            ok_qty=50,
            ng_qty=5,
        )

        self.assertEqual(
            self.tracker.total_ok_quantity,
            130,
        )
        self.assertEqual(
            self.tracker.total_ng_quantity,
            15,
        )
        self.assertEqual(
            self.tracker.total_produced_quantity,
            145,
        )

    def test_total_remaining_quantity(self) -> None:
        self.tracker.add(self.task_1)
        self.tracker.add(self.task_2)

        self.engine.ready(self.task_1)
        self.engine.start(self.task_1)
        self.engine.record_production(
            self.task_1,
            ok_qty=80,
            ng_qty=10,
        )

        self.assertEqual(
            self.tracker.total_remaining_quantity,
            90,
        )

    def test_completed_tasks(self) -> None:
        self.tracker.add(self.task_1)
        self.tracker.add(self.task_2)

        self.engine.ready(self.task_1)
        self.engine.start(self.task_1)
        self.engine.record_production(
            self.task_1,
            ok_qty=100,
        )

        self.assertEqual(
            self.tracker.completed_tasks,
            (self.task_1,),
        )

    def test_active_tasks(self) -> None:
        self.tracker.add(self.task_1)
        self.tracker.add(self.task_2)
        self.tracker.add(self.task_3)

        self.engine.ready(self.task_1)

        self.engine.ready(self.task_2)
        self.engine.start(self.task_2)

        self.assertEqual(
            len(self.tracker.active_tasks),
            2,
        )

    def test_contains_task(self) -> None:
        self.tracker.add(self.task_1)

        self.assertIn(
            self.task_1,
            self.tracker,
        )

    def test_iteration(self) -> None:
        self.tracker.add(self.task_1)
        self.tracker.add(self.task_2)

        self.assertEqual(
            tuple(self.tracker),
            (
                self.task_1,
                self.task_2,
            ),
        )

    def test_clear(self) -> None:
        self.tracker.add(self.task_1)
        self.tracker.add(self.task_2)

        self.tracker.clear()

        self.assertEqual(
            len(self.tracker),
            0,
        )

    def test_invalid_task_raises_error(self) -> None:
        with self.assertRaises(
            InvalidExecutionTaskError
        ):
            self.tracker.add(None)


if __name__ == "__main__":
    unittest.main()