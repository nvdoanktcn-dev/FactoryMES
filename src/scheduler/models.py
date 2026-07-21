from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.planning.models import PlanningResult
from src.planning.resource_models import ResourcePool
from src.scheduler.exceptions import (
    InvalidBookingError,
    InvalidScheduleInputError,
)


@dataclass(frozen=True, slots=True)
class MachineBooking:
    """
    Một khoảng thời gian máy được phân bổ cho một công đoạn.
    """

    work_order_code: str
    product_code: str
    machine_group: str
    machine_code: str
    op_code: str
    sequence: int
    start_time: datetime
    end_time: datetime
    quantity: int

    def __post_init__(self) -> None:
        work_order_code = self.work_order_code.strip()
        product_code = self.product_code.strip()
        machine_group = self.machine_group.strip().upper()
        machine_code = self.machine_code.strip().upper()
        op_code = self.op_code.strip().upper()

        if not work_order_code:
            raise InvalidBookingError(
                "Work order code must not be empty."
            )

        if not product_code:
            raise InvalidBookingError(
                "Product code must not be empty."
            )

        if not machine_group:
            raise InvalidBookingError(
                "Machine group must not be empty."
            )

        if not machine_code:
            raise InvalidBookingError(
                "Machine code must not be empty."
            )

        if not op_code:
            raise InvalidBookingError(
                "Operation code must not be empty."
            )

        if self.sequence <= 0:
            raise InvalidBookingError(
                "Operation sequence must be greater than zero."
            )

        if self.end_time <= self.start_time:
            raise InvalidBookingError(
                "Booking end time must be later than start time."
            )

        if self.quantity <= 0:
            raise InvalidBookingError(
                "Booking quantity must be greater than zero."
            )

        object.__setattr__(
            self,
            "work_order_code",
            work_order_code,
        )
        object.__setattr__(
            self,
            "product_code",
            product_code,
        )
        object.__setattr__(
            self,
            "machine_group",
            machine_group,
        )
        object.__setattr__(
            self,
            "machine_code",
            machine_code,
        )
        object.__setattr__(
            self,
            "op_code",
            op_code,
        )

    @property
    def duration_minutes(self) -> float:
        """
        Thời lượng booking tính bằng phút.
        """

        duration = self.end_time - self.start_time
        return duration.total_seconds() / 60.0


@dataclass(frozen=True, slots=True)
class ScheduleResult:
    """
    Kết quả lập lịch cho một công lệnh.
    """

    work_order_code: str
    product_code: str
    bookings: tuple[MachineBooking, ...]
    start_time: datetime
    finish_time: datetime

    def __post_init__(self) -> None:
        work_order_code = self.work_order_code.strip()
        product_code = self.product_code.strip()
        bookings = tuple(self.bookings)

        if not work_order_code:
            raise InvalidScheduleInputError(
                "Work order code must not be empty."
            )

        if not product_code:
            raise InvalidScheduleInputError(
                "Product code must not be empty."
            )

        if self.finish_time < self.start_time:
            raise InvalidScheduleInputError(
                "Schedule finish time must not be earlier "
                "than start time."
            )

        for booking in bookings:
            if booking.work_order_code != work_order_code:
                raise InvalidScheduleInputError(
                    "All bookings must belong to the same work order."
                )

            if booking.product_code != product_code:
                raise InvalidScheduleInputError(
                    "All bookings must belong to the same product."
                )

        object.__setattr__(
            self,
            "work_order_code",
            work_order_code,
        )
        object.__setattr__(
            self,
            "product_code",
            product_code,
        )
        object.__setattr__(
            self,
            "bookings",
            bookings,
        )

    @property
    def total_bookings(self) -> int:
        return len(self.bookings)

    @property
    def total_duration_minutes(self) -> float:
        duration = self.finish_time - self.start_time
        return duration.total_seconds() / 60.0


@dataclass(frozen=True, slots=True)
class SchedulerRequest:
    """
    Yêu cầu lập lịch sản xuất từ PlanningResult.
    """

    work_order_code: str
    planning_result: PlanningResult
    resource_pool: ResourcePool
    start_time: datetime

    def __post_init__(self) -> None:
        work_order_code = self.work_order_code.strip()

        if not work_order_code:
            raise InvalidScheduleInputError(
                "Work order code must not be empty."
            )

        if self.planning_result.request.demand_qty <= 0:
            raise InvalidScheduleInputError(
                "Planning demand quantity must be greater than zero."
            )

        if len(self.resource_pool) == 0:
            raise InvalidScheduleInputError(
                "Resource pool must not be empty."
            )

        object.__setattr__(
            self,
            "work_order_code",
            work_order_code,
        )

    @property
    def product_code(self) -> str:
        return self.planning_result.request.routing.product_code

    @property
    def demand_qty(self) -> int:
        return self.planning_result.request.demand_qty