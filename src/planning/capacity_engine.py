from __future__ import annotations

import math

from src.planning.exceptions import (
    InvalidCapacityInputError,
)


class CapacityEngine:
    """
    Bộ máy tính cân bằng công suất giữa các công đoạn.

    Công thức cơ bản:

        required_machines =
            ceil(current_cycle / reference_cycle)

    Ví dụ:
        reference = 20 giây
        current   = 40 giây
        kết quả   = 2 máy
    """

    @staticmethod
    def calculate_required_machines(
        reference_cycle_time_sec: float,
        current_cycle_time_sec: float,
    ) -> int:
        reference = CapacityEngine._validate_positive_number(
            reference_cycle_time_sec,
            "reference_cycle_time_sec",
        )
        current = CapacityEngine._validate_positive_number(
            current_cycle_time_sec,
            "current_cycle_time_sec",
        )

        return max(
            1,
            math.ceil(current / reference),
        )

    @staticmethod
    def calculate_utilization(
        reference_cycle_time_sec: float,
        current_cycle_time_sec: float,
        machine_count: int,
    ) -> float:
        """
        Tính tải tương đối của nhóm máy.

        Ví dụ:
            reference = 20 giây
            current = 40 giây
            machine_count = 2

            utilization = 40 / (20 * 2) = 1.0
        """

        reference = CapacityEngine._validate_positive_number(
            reference_cycle_time_sec,
            "reference_cycle_time_sec",
        )
        current = CapacityEngine._validate_positive_number(
            current_cycle_time_sec,
            "current_cycle_time_sec",
        )

        if isinstance(machine_count, bool):
            raise InvalidCapacityInputError(
                "machine_count must be a positive integer."
            )

        if not isinstance(machine_count, int):
            raise InvalidCapacityInputError(
                "machine_count must be an integer."
            )

        if machine_count <= 0:
            raise InvalidCapacityInputError(
                "machine_count must be greater than zero."
            )

        return current / (
            reference * machine_count
        )

    @staticmethod
    def calculate_effective_cycle_time(
        cycle_time_sec: float,
        machine_count: int,
    ) -> float:
        """
        Cycle time hiệu dụng sau khi chạy song song nhiều máy.

        Ví dụ:
            320 giây / 4 máy = 80 giây hiệu dụng.
        """

        cycle_time = CapacityEngine._validate_positive_number(
            cycle_time_sec,
            "cycle_time_sec",
        )

        if isinstance(machine_count, bool):
            raise InvalidCapacityInputError(
                "machine_count must be a positive integer."
            )

        if not isinstance(machine_count, int):
            raise InvalidCapacityInputError(
                "machine_count must be an integer."
            )

        if machine_count <= 0:
            raise InvalidCapacityInputError(
                "machine_count must be greater than zero."
            )

        return cycle_time / machine_count

    @staticmethod
    def calculate_required_machines_for_demand(
        demand_qty: int,
        cycle_time_sec: float,
        available_minutes: float,
        target_oee: float = 1.0,
    ) -> int:
        """
        Tính số máy cần thiết theo nhu cầu thực tế.

        required_seconds = demand_qty * cycle_time_sec
        effective_seconds_per_machine =
            available_minutes * 60 * target_oee
        """

        if isinstance(demand_qty, bool):
            raise InvalidCapacityInputError(
                "demand_qty must be a positive integer."
            )

        if not isinstance(demand_qty, int):
            raise InvalidCapacityInputError(
                "demand_qty must be an integer."
            )

        if demand_qty <= 0:
            raise InvalidCapacityInputError(
                "demand_qty must be greater than zero."
            )

        cycle_time = CapacityEngine._validate_positive_number(
            cycle_time_sec,
            "cycle_time_sec",
        )
        available = CapacityEngine._validate_positive_number(
            available_minutes,
            "available_minutes",
        )
        oee = CapacityEngine._validate_positive_number(
            target_oee,
            "target_oee",
        )

        if oee > 1:
            raise InvalidCapacityInputError(
                "target_oee must be less than or equal to 1."
            )

        required_seconds = demand_qty * cycle_time
        effective_seconds = available * 60 * oee

        return max(
            1,
            math.ceil(
                required_seconds / effective_seconds
            ),
        )

    @staticmethod
    def _validate_positive_number(
        value: float,
        field_name: str,
    ) -> float:
        if isinstance(value, bool):
            raise InvalidCapacityInputError(
                f"{field_name} must be a positive number."
            )

        try:
            number = float(value)
        except (TypeError, ValueError) as error:
            raise InvalidCapacityInputError(
                f"{field_name} must be a number."
            ) from error

        if not math.isfinite(number):
            raise InvalidCapacityInputError(
                f"{field_name} must be finite."
            )

        if number <= 0:
            raise InvalidCapacityInputError(
                f"{field_name} must be greater than zero."
            )

        return number