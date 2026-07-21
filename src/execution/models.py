from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.scheduler.models import MachineBooking
from src.execution.exceptions import (
    InvalidExecutionTaskError,
    InvalidProductionQuantityError,
)


class TaskStatus(str, Enum):
    WAITING = "WAITING"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"


@dataclass(slots=True)
class ExecutionTask:
    booking: MachineBooking
    status: TaskStatus = TaskStatus.WAITING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    ok_qty: int = 0
    ng_qty: int = 0
    downtime_minutes: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.booking, MachineBooking):
            raise InvalidExecutionTaskError(
                "booking must be a MachineBooking instance."
            )

        if not isinstance(self.status, TaskStatus):
            try:
                self.status = TaskStatus(
                    str(self.status).strip().upper()
                )
            except ValueError as exc:
                raise InvalidExecutionTaskError(
                    f"Invalid task status: {self.status}."
                ) from exc

        if self.ok_qty < 0:
            raise InvalidProductionQuantityError(
                "ok_qty must not be negative."
            )

        if self.ng_qty < 0:
            raise InvalidProductionQuantityError(
                "ng_qty must not be negative."
            )

        if self.downtime_minutes < 0:
            raise InvalidExecutionTaskError(
                "downtime_minutes must not be negative."
            )

        if (
            self.started_at is not None
            and self.finished_at is not None
            and self.finished_at < self.started_at
        ):
            raise InvalidExecutionTaskError(
                "finished_at must not be earlier than started_at."
            )

        if (
            self.status is TaskStatus.FINISHED
            and self.finished_at is None
        ):
            raise InvalidExecutionTaskError(
                "Finished task must have finished_at."
            )

    @property
    def work_order_code(self) -> str:
        return self.booking.work_order_code

    @property
    def product_code(self) -> str:
        return self.booking.product_code

    @property
    def machine_group(self) -> str:
        return self.booking.machine_group

    @property
    def machine_code(self) -> str:
        return self.booking.machine_code

    @property
    def op_code(self) -> str:
        return self.booking.op_code

    @property
    def sequence(self) -> int:
        return self.booking.sequence

    @property
    def planned_quantity(self) -> int:
        return self.booking.quantity

    @property
    def produced_quantity(self) -> int:
        return self.ok_qty + self.ng_qty

    @property
    def remaining_quantity(self) -> int:
        return max(
            self.planned_quantity - self.produced_quantity,
            0,
        )

    @property
    def is_completed(self) -> bool:
        return self.produced_quantity >= self.planned_quantity

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            TaskStatus.FINISHED,
            TaskStatus.CANCELLED,
        }

    @property
    def actual_runtime_minutes(self) -> float:
        if self.started_at is None:
            return 0.0

        end_time = self.finished_at or datetime.now()

        duration_seconds = (
            end_time - self.started_at
        ).total_seconds()

        return max(
            duration_seconds / 60.0
            - self.downtime_minutes,
            0.0,
        )

    def validate_quantity(
        self,
        ok_qty: int,
        ng_qty: int,
    ) -> None:
        if ok_qty < 0 or ng_qty < 0:
            raise InvalidProductionQuantityError(
                "Production quantity must not be negative."
            )

        if ok_qty + ng_qty > self.planned_quantity:
            raise InvalidProductionQuantityError(
                "Produced quantity must not exceed planned quantity."
            )