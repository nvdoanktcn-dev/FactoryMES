import unittest
from datetime import datetime, timedelta

from src.execution import (
    ExecutionCoordinator,
    ExecutionTask,
    MachineState,
    TaskStatus,
)
from src.execution.downtime import (
    DowntimeEvent,
    DowntimeReason,
)
from src.scheduler.models import MachineBooking
from src.services.execution_service import ExecutionService


class TestExecutionService(unittest.TestCase):

    def setUp(self):
        self.coordinator = ExecutionCoordinator()

        self.service = ExecutionService(
            coordinator=self.coordinator
        )

        now = datetime.now()

        self.booking = MachineBooking(
            work_order_code="WO001",
            product_code="P001",
            machine_group="CNC",
            machine_code="BL01",
            op_code="OP10",
            sequence=1,
            start_time=now,
            end_time=now + timedelta(hours=2),
            quantity=100,
        )

        self.task = ExecutionTask(
            booking=self.booking
        )

    def test_service_created(self):
        self.assertIs(
            self.service.coordinator,
            self.coordinator,
        )

    def test_register_task(self):
        result = self.service.register_task(
            self.task
        )

        self.assertIs(
            result,
            self.task,
        )

        self.assertEqual(
            self.service.get_machine_state("BL01"),
            MachineState.IDLE,
        )

    def test_ready_task(self):
        self.service.register_task(self.task)

        result = self.service.ready_task(
            self.task
        )

        self.assertIs(
            result,
            self.task,
        )

        self.assertEqual(
            self.task.status,
            TaskStatus.READY,
        )

    def test_start_task(self):
        self.service.register_task(self.task)
        self.service.ready_task(self.task)

        result = self.service.start_task(
            self.task
        )

        self.assertIs(
            result,
            self.task,
        )

        self.assertEqual(
            self.task.status,
            TaskStatus.RUNNING,
        )

        self.assertEqual(
            self.service.get_machine_state("BL01"),
            MachineState.RUNNING,
        )

    def test_pause_task(self):
        self.service.register_task(self.task)
        self.service.ready_task(self.task)
        self.service.start_task(self.task)

        result = self.service.pause_task(
            self.task
        )

        self.assertIs(
            result,
            self.task,
        )

        self.assertEqual(
            self.task.status,
            TaskStatus.PAUSED,
        )

        self.assertEqual(
            self.service.get_machine_state("BL01"),
            MachineState.PAUSED,
        )

    def test_resume_task(self):
        self.service.register_task(self.task)
        self.service.ready_task(self.task)
        self.service.start_task(self.task)
        self.service.pause_task(self.task)

        result = self.service.resume_task(
            self.task
        )

        self.assertIs(
            result,
            self.task,
        )

        self.assertEqual(
            self.task.status,
            TaskStatus.RUNNING,
        )

        self.assertEqual(
            self.service.get_machine_state("BL01"),
            MachineState.RUNNING,
        )

    def test_finish_task(self):
        self.service.register_task(self.task)
        self.service.ready_task(self.task)
        self.service.start_task(self.task)

        result = self.service.finish_task(
            self.task
        )

        self.assertIs(
            result,
            self.task,
        )

        self.assertEqual(
            self.task.status,
            TaskStatus.FINISHED,
        )

        self.assertIsNotNone(
            self.task.finished_at
        )

        self.assertEqual(
            self.service.get_machine_state("BL01"),
            MachineState.IDLE,
        )

    def test_cancel_task(self):
        self.service.register_task(self.task)

        result = self.service.cancel_task(
            self.task
        )

        self.assertIs(
            result,
            self.task,
        )

        self.assertEqual(
            self.task.status,
            TaskStatus.CANCELLED,
        )

    def test_record_production(self):
        self.service.register_task(self.task)
        self.service.ready_task(self.task)
        self.service.start_task(self.task)

        result = self.service.record_production(
            self.task,
            ok_qty=80,
            ng_qty=5,
        )

        self.assertIs(
            result,
            self.task,
        )

        self.assertEqual(
            self.task.ok_qty,
            80,
        )

        self.assertEqual(
            self.task.ng_qty,
            5,
        )

        self.assertEqual(
            self.task.produced_quantity,
            85,
        )

        self.assertEqual(
            self.task.remaining_quantity,
            15,
        )

    def test_record_production_auto_finish(self):
        self.service.register_task(self.task)
        self.service.ready_task(self.task)
        self.service.start_task(self.task)

        self.service.record_production(
            self.task,
            ok_qty=95,
            ng_qty=5,
        )

        self.assertEqual(
            self.task.status,
            TaskStatus.FINISHED,
        )

        self.assertTrue(
            self.task.is_completed
        )

        self.assertEqual(
            self.service.get_machine_state("BL01"),
            MachineState.IDLE,
        )

    def test_add_downtime(self):
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=30)

        event = DowntimeEvent(
            machine_code="BL01",
            work_order_code="WO001",
            reason=DowntimeReason.WAIT_MATERIAL,
            start_time=start_time,
            end_time=end_time,
            note="Waiting for material",
        )

        result = self.service.add_downtime(
            event
        )

        self.assertIs(
            result,
            event,
        )

        events = (
            self.coordinator
            .downtime_tracker
            .find_by_machine("BL01")
        )

        self.assertEqual(
            len(events),
            1,
        )

        self.assertIs(
            events[0],
            event,
        )

    def test_remove_downtime(self):
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=30)

        event = DowntimeEvent(
            machine_code="BL01",
            work_order_code="WO001",
            reason=DowntimeReason.REPAIR,
            start_time=start_time,
            end_time=end_time,
        )

        self.service.add_downtime(event)

        removed = self.service.remove_downtime(
            "BL01",
            start_time,
            end_time,
        )

        self.assertIs(
            removed,
            event,
        )

        events = (
            self.coordinator
            .downtime_tracker
            .find_by_machine("BL01")
        )

        self.assertEqual(
            events,
            (),
        )

    def test_get_machine_history(self):
        self.service.register_task(self.task)
        self.service.ready_task(self.task)
        self.service.start_task(self.task)
        self.service.pause_task(self.task)
        self.service.resume_task(self.task)

        history = self.service.get_machine_history(
            "BL01"
        )

        self.assertGreaterEqual(
            len(history),
            4,
        )

    def test_get_machine_tasks(self):
        self.service.register_task(self.task)

        tasks = self.service.get_machine_tasks(
            "BL01"
        )

        self.assertEqual(
            len(tasks),
            1,
        )

        self.assertIs(
            tasks[0],
            self.task,
        )


if __name__ == "__main__":
    unittest.main()