from __future__ import annotations

from src.planning.capacity_engine import CapacityEngine
from src.planning.models import (
    CapacityResult,
    Operation,
    Routing,
    RoutingAnalysis,
)
from src.planning.routing_validator import (
    RoutingValidator,
)


class RoutingEngine:
    """Phân tích tuyến công nghệ và cân bằng số máy theo OP."""

    def __init__(
        self,
        capacity_engine: CapacityEngine | None = None,
    ) -> None:
        self.capacity_engine = (
            capacity_engine
            or CapacityEngine()
        )

    def find_bottleneck(
        self,
        routing: Routing,
    ) -> Operation:
        """
        Tìm công đoạn có cycle time lớn nhất.

        Khi nhiều OP có cùng cycle time, lấy OP có sequence nhỏ hơn.
        """

        RoutingValidator.validate(routing)

        return max(
            routing.operations,
            key=lambda operation: (
                operation.cycle_time_sec,
                -operation.sequence,
            ),
        )

    def build_capacity_profile(
        self,
        routing: Routing,
        reference_sequence: int | None = None,
    ) -> tuple[CapacityResult, ...]:
        """
        Tạo hồ sơ công suất cho toàn bộ routing.

        Mặc định OP đầu tiên là công đoạn tham chiếu.
        Có thể truyền reference_sequence để chọn OP khác.
        """

        RoutingValidator.validate(routing)

        operations = routing.sorted_operations()
        reference = self._get_reference_operation(
            operations,
            reference_sequence,
        )
        bottleneck = self.find_bottleneck(routing)

        results: list[CapacityResult] = []

        for operation in operations:
            required_machines = (
                self.capacity_engine
                .calculate_required_machines(
                    reference.cycle_time_sec,
                    operation.cycle_time_sec,
                )
            )

            utilization = (
                self.capacity_engine
                .calculate_utilization(
                    reference.cycle_time_sec,
                    operation.cycle_time_sec,
                    required_machines,
                )
            )

            results.append(
                CapacityResult(
                    op_code=operation.op_code,
                    sequence=operation.sequence,
                    machine_group=operation.machine_group,
                    cycle_time_sec=operation.cycle_time_sec,
                    reference_cycle_time_sec=(
                        reference.cycle_time_sec
                    ),
                    required_machines=required_machines,
                    utilization=utilization,
                    is_bottleneck=(
                        operation.op_code
                        == bottleneck.op_code
                    ),
                )
            )

        return tuple(results)

    def analyze(
        self,
        routing: Routing,
        reference_sequence: int | None = None,
    ) -> RoutingAnalysis:
        """Phân tích đầy đủ routing."""

        RoutingValidator.validate(routing)

        bottleneck = self.find_bottleneck(routing)
        capacities = self.build_capacity_profile(
            routing,
            reference_sequence=reference_sequence,
        )

        return RoutingAnalysis(
            product_code=routing.product_code,
            capacities=capacities,
            bottleneck=bottleneck,
        )

    @staticmethod
    def _get_reference_operation(
        operations: list[Operation],
        reference_sequence: int | None,
    ) -> Operation:
        if reference_sequence is None:
            return operations[0]

        for operation in operations:
            if operation.sequence == reference_sequence:
                return operation

        raise ValueError(
            "Reference operation was not found: "
            f"sequence={reference_sequence}."
        )