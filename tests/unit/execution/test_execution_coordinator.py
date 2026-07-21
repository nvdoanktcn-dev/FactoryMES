import unittest
from datetime import datetime, timedelta

from src.scheduler.models import MachineBooking
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

class TestExecutionCoordinator(unittest.TestCase):

    def setUp(self):
        self.coordinator = ExecutionCoordinator()

        now = datetime.now()

        booking = MachineBooking(
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
            booking=booking,
        )

    def test_register_task(self):
        self.coordinator.register_task(self.task)

        self.assertEqual(
            len(self.coordinator.execution_tracker),
                1,
        )

        self.assertEqual(
            self.coordinator.get_machine_state("BL01"),
            MachineState.IDLE,
        )

    def test_start_task(self):
        self.coordinator.register_task(self.task)

        self.coordinator.start_task(self.task)

        self.assertEqual(
            self.task.status,
            TaskStatus.RUNNING,
        )

        self.assertEqual(
            self.coordinator.get_machine_state("BL01"),
            MachineState.RUNNING,
        )

    def test_pause_task(self):
        self.coordinator.register_task(self.task)
        self.coordinator.start_task(self.task)

        self.coordinator.pause_task(self.task)

        self.assertEqual(
            self.task.status,
            TaskStatus.PAUSED,
        )

        self.assertEqual(
            self.coordinator.get_machine_state("BL01"),
            MachineState.PAUSED,
        )

    def test_resume_task(self):
        self.coordinator.register_task(self.task)

        self.coordinator.start_task(self.task)
        self.coordinator.pause_task(self.task)

        self.coordinator.resume_task(self.task)

        self.assertEqual(
            self.task.status,
            TaskStatus.RUNNING,
        )
    
        self.assertEqual(
            self.coordinator.get_machine_state("BL01"),
            MachineState.RUNNING,
        )

    def test_finish_task(self):
        self.coordinator.register_task(self.task)

        self.coordinator.start_task(self.task)

        self.coordinator.finish_task(self.task)

        self.assertEqual(
            self.task.status,
            TaskStatus.FINISHED,
        )

        self.assertEqual(
            self.coordinator.get_machine_state("BL01"),
            MachineState.IDLE,
        )

    def test_record_production_auto_finish(self):
        self.coordinator.register_task(self.task)
        self.coordinator.start_task(self.task)

        self.coordinator.record_production(
            self.task,
            ok_qty=100,
        )

        self.assertEqual(
            self.task.status,
            TaskStatus.FINISHED,
        )

        self.assertEqual(
            self.coordinator.get_machine_state("BL01"),
            MachineState.IDLE,
        )

    def test_add_downtime(self):
        self.coordinator.register_task(self.task)
        self.coordinator.start_task(self.task)

        event = DowntimeEvent(
            machine_code="BL01",
                work_order_code="WO001",
            start_time=datetime(2026, 7, 20, 8, 0),
            end_time=datetime(2026, 7, 20, 8, 30),
            reason=DowntimeReason.MAINTENANCE,
        )

        self.coordinator.add_downtime(event)

        self.assertEqual(
            self.coordinator.get_machine_state("BL01"),
            MachineState.DOWNTIME,
        )

    def test_machine_history(self):
        self.coordinator.register_task(self.task)

        self.coordinator.start_task(self.task)
        self.coordinator.pause_task(self.task)
        self.coordinator.resume_task(self.task)
        self.coordinator.finish_task(self.task)

        history = self.coordinator.get_machine_history("BL01")

        self.assertEqual(len(history), 5)

        self.assertEqual(
            history[0].current_state,
            MachineState.IDLE,
        )

        self.assertEqual(
            history[-1].current_state,
            MachineState.IDLE,
        )