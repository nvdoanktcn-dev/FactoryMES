from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Operation:
    """
    Một công đoạn trong quy trình sản xuất.

    Attributes:
        op_code:
            Mã công đoạn, ví dụ OP10, OP20.

        sequence:
            Thứ tự thực hiện công đoạn.

        machine_group:
            Nhóm máy thực hiện công đoạn, ví dụ CNC, ROBOT, ASK.

        cycle_time_sec:
            Thời gian chu kỳ của một sản phẩm, tính bằng giây.

        setup_time_min:
            Thời gian chuẩn bị máy, tính bằng phút.

        employee_required:
            Số nhân viên cần cho công đoạn.

        standard_qty:
            Sản lượng tiêu chuẩn dùng cho công đoạn.
    """

    op_code: str
    sequence: int
    machine_group: str
    cycle_time_sec: float
    setup_time_min: float = 0.0
    employee_required: int = 1
    standard_qty: int = 1


@dataclass(frozen=True, slots=True)
class Routing:
    """
    Quy trình sản xuất của một sản phẩm.
    """

    product_code: str
    operations: tuple[Operation, ...] | list[Operation]

    def __post_init__(self) -> None:
        # Chuẩn hóa list thành tuple để giữ tính bất biến của dataclass.
        object.__setattr__(
            self,
            "operations",
            tuple(self.operations),
        )

    def sorted_operations(self) -> tuple[Operation, ...]:
        """
        Trả về các công đoạn theo thứ tự sequence tăng dần.
        """

        return tuple(
            sorted(
                self.operations,
                key=lambda operation: operation.sequence,
            )
        )


@dataclass(frozen=True, slots=True)
class CapacityResult:
    op_code: str
    sequence: int
    machine_group: str

    cycle_time_sec: float

    reference_cycle_time_sec: float

    required_machines: int

    utilization: float

    is_bottleneck: bool = False

@dataclass(frozen=True, slots=True)
class RoutingAnalysis:
    product_code: str

    capacities: tuple[CapacityResult, ...]

    bottleneck: Operation

    def __post_init__(self):
        object.__setattr__(
            self,
            "capacities",
            tuple(self.capacities),
        )

    @property
    def total_operations(self):
        return len(self.capacities)

    @property
    def maximum_required_machines(self):
        if not self.capacities:
            return 0

        return max(
            c.required_machines
            for c in self.capacities
        )

@dataclass(frozen=True, slots=True)
class PlanningRequest:
    """
    Yêu cầu phân tích và lập kế hoạch cho một Routing.
    """

    routing: Routing
    demand_qty: int
    available_minutes: float
    target_oee: float = 0.85
    reference_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class OperationPlan:
    """
    Kế hoạch công suất của một công đoạn.
    """

    operation: Operation
    required_machines: int
    estimated_runtime_minutes: float
    utilization: float
    is_bottleneck: bool


@dataclass(frozen=True, slots=True)
class PlanningResult:
    """
    Kết quả tổng hợp từ PlanningService.
    """

    request: PlanningRequest
    routing_analysis: RoutingAnalysis
    operation_plans: tuple[OperationPlan, ...]
    total_required_machines: int
    estimated_runtime_minutes: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "operation_plans",
            tuple(self.operation_plans),
        )