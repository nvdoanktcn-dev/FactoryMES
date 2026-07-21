from __future__ import annotations

from datetime import datetime

from src.execution.exceptions import (
    InvalidExecutionTaskError,
    InvalidTaskTransitionError,
    TaskAlreadyFinishedError,
)
from src.execution.models import (
    ExecutionTask,
    TaskStatus,
)


class ExecutionEngine:
    """Quản lý vòng đời và sản lượng của ExecutionTask."""

    _ALLOWED_TRANSITIONS: dict[
        TaskStatus,
        set[TaskStatus],
    ] = {
        TaskStatus.WAITING: {
            TaskStatus.READY,
            TaskStatus.CANCELLED,
        },
        TaskStatus.READY: {
            TaskStatus.RUNNING,
            TaskStatus.CANCELLED,
        },
        TaskStatus.RUNNING: {
            TaskStatus.PAUSED,
            TaskStatus.FINISHED,
            TaskStatus.CANCELLED,
        },
        TaskStatus.PAUSED: {
            TaskStatus.RUNNING,
            TaskStatus.CANCELLED,
        },
        TaskStatus.FINISHED: set(),
        TaskStatus.CANCELLED: set(),
    }

    def ready(self, task: ExecutionTask) -> None:
        self._transition(
            task,
            TaskStatus.READY,
        )

    def start(self, task: ExecutionTask) -> None:
        self._transition(
            task,
            TaskStatus.RUNNING,
        )

    def pause(self, task: ExecutionTask) -> None:
        self._transition(
            task,
            TaskStatus.PAUSED,
        )

    def resume(self, task: ExecutionTask) -> None:
        self._transition(
            task,
            TaskStatus.RUNNING,
        )

    def finish(self, task: ExecutionTask) -> None:
        self._transition(
            task,
            TaskStatus.FINISHED,
        )

    def cancel(self, task: ExecutionTask) -> None:
        self._transition(
            task,
            TaskStatus.CANCELLED,
        )

    def record_production(
        self,
        task: ExecutionTask,
        ok_qty: int,
        ng_qty: int = 0,
    ) -> None:
        """
        Cộng dồn sản lượng thực tế.

        Chỉ được ghi nhận khi task đang RUNNING.
        Task tự kết thúc khi tổng OK + NG đạt kế hoạch.
        """
        self._validate_task(task)

        if task.status is TaskStatus.FINISHED:
            raise TaskAlreadyFinishedError(
                "Cannot record production for a finished task."
            )

        if task.status is not TaskStatus.RUNNING:
            raise InvalidTaskTransitionError(
                "Production can only be recorded "
                "while task status is RUNNING."
            )

        new_ok_qty = task.ok_qty + ok_qty
        new_ng_qty = task.ng_qty + ng_qty

        task.validate_quantity(
            ok_qty=new_ok_qty,
            ng_qty=new_ng_qty,
        )

        task.ok_qty = new_ok_qty
        task.ng_qty = new_ng_qty

        if task.is_completed:
            self.finish(task)

    def _transition(
        self,
        task: ExecutionTask,
        new_status: TaskStatus,
    ) -> None:
        self._validate_task(task)

        if task.status is TaskStatus.FINISHED:
            raise TaskAlreadyFinishedError(
                "Finished task cannot change state."
            )

        allowed_statuses = self._ALLOWED_TRANSITIONS.get(
            task.status,
            set(),
        )

        if new_status not in allowed_statuses:
            raise InvalidTaskTransitionError(
                f"{task.status.value} -> "
                f"{new_status.value} is not allowed."
            )

        now = datetime.now()

        if (
            new_status is TaskStatus.RUNNING
            and task.started_at is None
        ):
            task.started_at = now

        if new_status is TaskStatus.FINISHED:
            task.finished_at = now

        task.status = new_status

    @staticmethod
    def _validate_task(
        task: ExecutionTask,
    ) -> None:
        if not isinstance(task, ExecutionTask):
            raise InvalidExecutionTaskError(
                "task must be an ExecutionTask instance."
            )
            
