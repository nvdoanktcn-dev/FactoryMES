from __future__ import annotations

from datetime import datetime

from src.execution import (
    ExecutionCoordinator,
    ExecutionTask,
    MachineState,
)
from src.execution.downtime import DowntimeEvent


class ExecutionService:
    """
    Application service cho Production Execution.

    Service là lớp trung gian giữa UI/Controller
    và ExecutionCoordinator.
    """

    def __init__(
        self,
        coordinator: ExecutionCoordinator | None = None,
    ) -> None:
        self.coordinator = (
            coordinator
            if coordinator is not None
            else ExecutionCoordinator()
        )

    def register_task(
        self,
        task: ExecutionTask,
    ) -> ExecutionTask:
        return self.coordinator.register_task(task)

    def ready_task(
        self,
        task: ExecutionTask,
    ) -> ExecutionTask:
        return self.coordinator.ready_task(task)

    def start_task(
        self,
        task: ExecutionTask,
    ) -> ExecutionTask:
        return self.coordinator.start_task(task)

    def pause_task(
        self,
        task: ExecutionTask,
    ) -> ExecutionTask:
        return self.coordinator.pause_task(task)

    def resume_task(
        self,
        task: ExecutionTask,
    ) -> ExecutionTask:
        return self.coordinator.resume_task(task)

    def finish_task(
        self,
        task: ExecutionTask,
    ) -> ExecutionTask:
        return self.coordinator.finish_task(task)

    def cancel_task(
        self,
        task: ExecutionTask,
    ) -> ExecutionTask:
        return self.coordinator.cancel_task(task)

    def record_production(
        self,
        task: ExecutionTask,
        *,
        ok_qty: int = 0,
        ng_qty: int = 0,
    ) -> ExecutionTask:
        return self.coordinator.record_production(
            task,
            ok_qty=ok_qty,
            ng_qty=ng_qty,
        )

    def add_downtime(
        self,
        event: DowntimeEvent,
    ) -> DowntimeEvent:
        return self.coordinator.add_downtime(event)

    def remove_downtime(
        self,
        machine_code: str,
        start_time: datetime,
        end_time: datetime,
    ) -> DowntimeEvent:
        return self.coordinator.remove_downtime(
            machine_code,
            start_time,
            end_time,
        )

    def get_machine_state(
        self,
        machine_code: str,
    ) -> MachineState:
        return self.coordinator.get_machine_state(
            machine_code
        )

    def get_machine_history(
        self,
        machine_code: str,
    ):
        return self.coordinator.get_machine_history(
            machine_code
        )

    def get_machine_tasks(
        self,
        machine_code: str,
    ) -> tuple[ExecutionTask, ...]:
        return self.coordinator.get_machine_tasks(
            machine_code
        )