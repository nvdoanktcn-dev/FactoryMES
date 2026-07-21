from __future__ import annotations

from datetime import datetime, timedelta
from math import ceil

from src.scheduler.exceptions import (
    InsufficientResourceError,
    InvalidScheduleInputError,
)
from src.scheduler.models import (
    MachineBooking,
    SchedulerRequest,
    ScheduleResult,
)


class SchedulerEngine:
    """
    Chuyển PlanningResult thành lịch sản xuất.

    Phiên bản Phase 1:
        - Lập lịch cho một công lệnh.
        - OP chạy theo thứ tự sequence.
        - Nhiều máy trong cùng OP chạy song song.
        - OP tiếp theo bắt đầu sau khi OP trước hoàn tất.
        - Chưa xét ca làm việc, bảo trì và lịch máy hiện có.
    """

    def create_schedule(
        self,
        request: SchedulerRequest,
    ) -> ScheduleResult:
        operation_plans = sorted(
            request.planning_result.operation_plans,
            key=lambda item: item.operation.sequence,
        )

        if not operation_plans:
            raise InvalidScheduleInputError(
                "Planning result must contain at least one operation plan."
            )

        bookings: list[MachineBooking] = []
        current_time = request.start_time

        for operation_plan in operation_plans:
            operation_bookings = self._schedule_operation(
                request=request,
                operation_plan=operation_plan,
                start_time=current_time,
            )

            bookings.extend(operation_bookings)

            # Các máy của cùng một OP chạy song song.
            # OP sau chỉ bắt đầu khi toàn bộ booking của OP trước hoàn tất.
            current_time = max(
                booking.end_time
                for booking in operation_bookings
            )

        return ScheduleResult(
            work_order_code=request.work_order_code,
            product_code=request.product_code,
            bookings=tuple(bookings),
            start_time=request.start_time,
            finish_time=current_time,
        )

    def _schedule_operation(
        self,
        request: SchedulerRequest,
        operation_plan,
        start_time: datetime,
    ) -> tuple[MachineBooking, ...]:
        operation = operation_plan.operation
        required_machines = operation_plan.required_machines

        if required_machines <= 0:
            raise InvalidScheduleInputError(
                f"Required machines must be greater than zero: "
                f"{operation.op_code}."
            )

        resource = self._get_resource(
            request=request,
            machine_group=operation.machine_group,
        )

        if resource.available_machines < required_machines:
            raise InsufficientResourceError(
                "Insufficient machines for "
                f"{operation.op_code}: "
                f"required={required_machines}, "
                f"available={resource.available_machines}, "
                f"group={operation.machine_group}."
            )

        runtime_minutes = (
            operation_plan.estimated_runtime_minutes
        )

        if runtime_minutes <= 0:
            raise InvalidScheduleInputError(
                f"Estimated runtime must be greater than zero: "
                f"{operation.op_code}."
            )

        end_time = start_time + timedelta(
            minutes=runtime_minutes
        )

        quantities = self._distribute_quantity(
            total_quantity=request.demand_qty,
            machine_count=required_machines,
        )

        bookings = []

        for machine_index, quantity in enumerate(
            quantities,
            start=1,
        ):
            bookings.append(
                MachineBooking(
                    work_order_code=request.work_order_code,
                    product_code=request.product_code,
                    machine_group=operation.machine_group,
                    machine_code=self._build_machine_code(
                        operation.machine_group,
                        machine_index,
                    ),
                    op_code=operation.op_code,
                    sequence=operation.sequence,
                    start_time=start_time,
                    end_time=end_time,
                    quantity=quantity,
                )
            )

        return tuple(bookings)

    @staticmethod
    def _get_resource(
        request: SchedulerRequest,
        machine_group: str,
    ):
        try:
            return request.resource_pool.get(machine_group)
        except Exception as exc:
            raise InsufficientResourceError(
                f"Machine resource was not found: {machine_group}."
            ) from exc

    @staticmethod
    def _build_machine_code(
        machine_group: str,
        machine_index: int,
    ) -> str:
        normalized_group = (
            machine_group.strip().upper()
        )

        return f"{normalized_group}{machine_index:02d}"

    @staticmethod
    def _distribute_quantity(
        total_quantity: int,
        machine_count: int,
    ) -> tuple[int, ...]:
        """
        Chia sản lượng cho các máy.

        Ví dụ:
            100 PCS / 3 máy -> (34, 33, 33)
        """

        if total_quantity <= 0:
            raise InvalidScheduleInputError(
                "Total quantity must be greater than zero."
            )

        if machine_count <= 0:
            raise InvalidScheduleInputError(
                "Machine count must be greater than zero."
            )

        base_quantity = total_quantity // machine_count
        remainder = total_quantity % machine_count

        quantities = []

        for index in range(machine_count):
            quantity = base_quantity

            if index < remainder:
                quantity += 1

            # MachineBooking không cho phép quantity bằng 0.
            # Không tạo máy dư khi số máy lớn hơn sản lượng.
            if quantity > 0:
                quantities.append(quantity)

        return tuple(quantities)