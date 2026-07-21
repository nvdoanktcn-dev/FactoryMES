from __future__ import annotations

from collections.abc import Iterator

from src.execution.exceptions import (
    DuplicateExecutionTaskError,
    ExecutionTaskNotFoundError,
    InvalidExecutionTaskError,
)
from src.execution.models import (
    ExecutionTask,
    TaskStatus,
)


class ExecutionTracker:
    """
    Lưu trữ và tổng hợp các ExecutionTask trong bộ nhớ.

    Tracker không thay đổi trạng thái task.
    Việc thay đổi trạng thái thuộc trách nhiệm ExecutionEngine.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, ExecutionTask] = {}

    def add(self, task: ExecutionTask) -> None:
        self._validate_task(task)

        key = self._build_key(task)

        if key in self._tasks:
            raise DuplicateExecutionTaskError(
                f"Execution task already exists: {key}."
            )

        self._tasks[key] = task

    def get(
        self,
        machine_code: str,
        work_order_code: str,
        op_code: str,
    ) -> ExecutionTask:
        key = self._build_key_from_values(
            machine_code=machine_code,
            work_order_code=work_order_code,
            op_code=op_code,
        )

        try:
            return self._tasks[key]
        except KeyError as exc:
            raise ExecutionTaskNotFoundError(
                f"Execution task not found: {key}."
            ) from exc

    def remove(
        self,
        machine_code: str,
        work_order_code: str,
        op_code: str,
    ) -> ExecutionTask:
        key = self._build_key_from_values(
            machine_code=machine_code,
            work_order_code=work_order_code,
            op_code=op_code,
        )

        try:
            return self._tasks.pop(key)
        except KeyError as exc:
            raise ExecutionTaskNotFoundError(
                f"Execution task not found: {key}."
            ) from exc

    def find_by_machine(
        self,
        machine_code: str,
    ) -> tuple[ExecutionTask, ...]:
        normalized_machine = self._normalize(machine_code)

        return tuple(
            task
            for task in self._tasks.values()
            if self._normalize(task.machine_code)
            == normalized_machine
        )

    def find_by_work_order(
        self,
        work_order_code: str,
    ) -> tuple[ExecutionTask, ...]:
        normalized_work_order = self._normalize(
            work_order_code
        )

        return tuple(
            task
            for task in self._tasks.values()
            if self._normalize(task.work_order_code)
            == normalized_work_order
        )

    def find_by_product(
        self,
        product_code: str,
    ) -> tuple[ExecutionTask, ...]:
        normalized_product = self._normalize(
            product_code
        )

        return tuple(
            task
            for task in self._tasks.values()
            if self._normalize(task.product_code)
            == normalized_product
        )

    def find_by_status(
        self,
        status: TaskStatus,
    ) -> tuple[ExecutionTask, ...]:
        if not isinstance(status, TaskStatus):
            try:
                status = TaskStatus(
                    str(status).strip().upper()
                )
            except ValueError as exc:
                raise InvalidExecutionTaskError(
                    f"Invalid task status: {status}."
                ) from exc

        return tuple(
            task
            for task in self._tasks.values()
            if task.status is status
        )

    @property
    def total_tasks(self) -> int:
        return len(self._tasks)

    @property
    def total_planned_quantity(self) -> int:
        return sum(
            task.planned_quantity
            for task in self._tasks.values()
        )

    @property
    def total_ok_quantity(self) -> int:
        return sum(
            task.ok_qty
            for task in self._tasks.values()
        )

    @property
    def total_ng_quantity(self) -> int:
        return sum(
            task.ng_qty
            for task in self._tasks.values()
        )

    @property
    def total_produced_quantity(self) -> int:
        return (
            self.total_ok_quantity
            + self.total_ng_quantity
        )

    @property
    def total_remaining_quantity(self) -> int:
        return sum(
            task.remaining_quantity
            for task in self._tasks.values()
        )

    @property
    def completed_tasks(self) -> tuple[ExecutionTask, ...]:
        return self.find_by_status(
            TaskStatus.FINISHED
        )

    @property
    def active_tasks(self) -> tuple[ExecutionTask, ...]:
        active_statuses = {
            TaskStatus.READY,
            TaskStatus.RUNNING,
            TaskStatus.PAUSED,
        }

        return tuple(
            task
            for task in self._tasks.values()
            if task.status in active_statuses
        )

    def clear(self) -> None:
        self._tasks.clear()

    def __len__(self) -> int:
        return len(self._tasks)

    def __iter__(self) -> Iterator[ExecutionTask]:
        return iter(self._tasks.values())

    def __contains__(
        self,
        task: object,
    ) -> bool:
        if not isinstance(task, ExecutionTask):
            return False

        return self._build_key(task) in self._tasks

    @classmethod
    def _build_key(
        cls,
        task: ExecutionTask,
    ) -> str:
        return cls._build_key_from_values(
            machine_code=task.machine_code,
            work_order_code=task.work_order_code,
            op_code=task.op_code,
        )

    @classmethod
    def _build_key_from_values(
        cls,
        machine_code: str,
        work_order_code: str,
        op_code: str,
    ) -> str:
        machine = cls._normalize_required(
            machine_code,
            "machine_code",
        )
        work_order = cls._normalize_required(
            work_order_code,
            "work_order_code",
        )
        operation = cls._normalize_required(
            op_code,
            "op_code",
        )

        return f"{machine}|{work_order}|{operation}"

    @staticmethod
    def _normalize(value: str) -> str:
        return str(value).strip().upper()

    @classmethod
    def _normalize_required(
        cls,
        value: str,
        field_name: str,
    ) -> str:
        normalized = cls._normalize(value)

        if not normalized:
            raise InvalidExecutionTaskError(
                f"{field_name} must not be empty."
            )

        return normalized

    @staticmethod
    def _validate_task(
        task: ExecutionTask,
    ) -> None:
        if not isinstance(task, ExecutionTask):
            raise InvalidExecutionTaskError(
                "task must be an ExecutionTask instance."
            )

