from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time

from src.framework.exception import NotFoundError, ValidationError
from src.planning.capacity_engine import CapacityEngine
from src.planning.exceptions import PlanningError
from src.planning.models import Operation, PlanningRequest, Routing
from src.planning.planning_service import PlanningService
from src.planning.resource_models import MachineResource, ResourcePool
from src.scheduler.exceptions import SchedulerError
from src.scheduler.models import SchedulerRequest
from src.scheduler.scheduler_engine import SchedulerEngine
from src.services.base_service import SessionOwnedService
from src.services.machine_service import MachineService
from src.services.routing_service import RoutingService
from src.services.work_order_service import WorkOrderService


# ==============================================================
# Kết quả trả về (UI-facing, không phải core engine dataclass)
# ==============================================================

@dataclass
class MachineBalanceRow:
    """
    Một dòng trong bảng Capacity / Machine Balance cho một OP.
    """

    op_code: str
    sequence: int
    machine_group: str
    cycle_time_sec: float

    # Số máy cần để cân bằng thông lượng với OP nghẽn (bottleneck) -
    # đây là số THỰC SỰ được dùng để lập lịch (SchedulerEngine).
    required_machines_balance: int

    utilization_percent: float
    is_bottleneck: bool

    # Số máy cần để đạt demand_qty trong available_minutes với
    # target_oee - tính riêng cho OP này, KHÔNG phụ thuộc cân bằng với
    # OP khác (thông tin tham khảo thêm, không dùng để lập lịch).
    required_machines_for_demand: int

    available_machines: int
    shortage: int

    @property
    def has_shortage(self) -> bool:
        return self.shortage > 0


@dataclass
class ProductionPlanResult:
    """
    Kết quả phân tích + lập lịch cho một Work Order - trả về từ
    ProductionPlanningService.analyze_work_order().
    """

    work_order_no: str
    product_code: str
    demand_qty: int
    available_minutes: float
    target_oee: float

    total_required_machines: int
    estimated_runtime_minutes: float
    bottleneck_op_code: str

    balance_rows: list = field(default_factory=list)

    schedule_bookings: list = field(default_factory=list)
    schedule_start: datetime | None = None
    schedule_finish: datetime | None = None

    # None nếu lập lịch thành công; có giá trị nếu lập lịch thất bại
    # (VD: thiếu máy) - Capacity/Machine Balance vẫn có giá trị dùng
    # được ngay cả khi Scheduling thất bại, nên không raise exception.
    schedule_error: str | None = None

    @property
    def has_shortage(self) -> bool:
        return any(row.has_shortage for row in self.balance_rows)


class ProductionPlanningService(SessionOwnedService):
    """
    Giai đoạn 5 (Production Planning, 2026-07-25).

    Facade nối các engine tính toán thuần (đã có sẵn, chưa từng được
    dùng ở đâu trong app) - RoutingEngine/CapacityEngine (qua
    PlanningService) và SchedulerEngine - với dữ liệu THẬT trong
    database: Work Order (nhu cầu sản lượng), Routing (quy trình sản
    xuất của sản phẩm), Machine (số máy thực tế hiện có theo từng
    machine_type) - để tạo ra 1 bản phân tích Capacity/Machine Balance
    và 1 lịch sản xuất dự kiến (Scheduling) cho một Work Order.
    """

    DEFAULT_AVAILABLE_MINUTES = 480.0
    DEFAULT_TARGET_OEE = 0.85

    # Chỉ máy đang thực sự chạy (RUNNING) mới được tính là công suất
    # khả dụng để lập kế hoạch/lập lịch. STOPPED/MAINTENANCE/INACTIVE
    # đều KHÔNG khả dụng - đây là chủ đích, không phải sơ suất (một
    # máy đang bảo trì hoặc dừng không thể nhận thêm việc mới).
    AVAILABLE_MACHINE_STATUSES = {
        "RUNNING",
    }

    def __init__(
        self,
        session=None,
        routing_service=None,
        work_order_service=None,
        machine_service=None,
        planning_service=None,
        scheduler_engine=None,
    ) -> None:
        super().__init__(session=session)

        self.routing_service = routing_service or RoutingService(
            session=self.session
        )
        self.work_order_service = work_order_service or WorkOrderService(
            session=self.session
        )
        self.machine_service = machine_service or MachineService(
            session=self.session
        )

        # Engine thuần, không cần Session - dùng chung một instance.
        self.planning_service = planning_service or PlanningService()
        self.scheduler_engine = scheduler_engine or SchedulerEngine()

    # ==========================================================
    # Danh sách Work Order có thể lập kế hoạch (cho combo box UI)
    # ==========================================================

    def list_plannable_work_orders(self):
        return self.work_order_service.get_open_orders()

    # ==========================================================
    # Phân tích + lập lịch chính
    # ==========================================================

    def analyze_work_order(
        self,
        work_order_no,
        available_minutes=None,
        target_oee=None,
        reference_sequence=None,
        schedule_start_time=None,
    ) -> ProductionPlanResult:
        available_minutes = float(
            available_minutes or self.DEFAULT_AVAILABLE_MINUTES
        )
        target_oee = float(
            target_oee or self.DEFAULT_TARGET_OEE
        )

        work_order = self.work_order_service.get_by_no(work_order_no)

        if work_order is None:
            raise NotFoundError(
                f"Work Order not found: {work_order_no}"
            )

        if not work_order.plan_qty or work_order.plan_qty <= 0:
            raise ValidationError(
                f"Work Order {work_order.work_order_no} has no "
                "valid Plan Qty (must be greater than zero)."
            )

        routing_rows = self.routing_service.get_product_routing(
            work_order.product_code
        )

        if not routing_rows:
            raise ValidationError(
                "No Routing defined for product "
                f"{work_order.product_code} - cannot plan. Please "
                "create a Routing for this product first."
            )

        operations = [
            self._map_operation(row) for row in routing_rows
        ]

        routing = Routing(
            product_code=work_order.product_code,
            operations=operations,
        )

        request = PlanningRequest(
            routing=routing,
            demand_qty=int(work_order.plan_qty),
            available_minutes=available_minutes,
            target_oee=target_oee,
            reference_sequence=reference_sequence,
        )

        try:
            planning_result = self.planning_service.analyze(request)
        except PlanningError as error:
            raise ValidationError(str(error)) from error

        resource_pool = self._build_resource_pool(target_oee)

        balance_rows = self._build_balance_rows(
            planning_result=planning_result,
            demand_qty=int(work_order.plan_qty),
            available_minutes=available_minutes,
            target_oee=target_oee,
            resource_pool=resource_pool,
        )

        (
            schedule_bookings,
            schedule_start,
            schedule_finish,
            schedule_error,
        ) = self._try_build_schedule(
            work_order=work_order,
            planning_result=planning_result,
            resource_pool=resource_pool,
            schedule_start_time=schedule_start_time,
        )

        return ProductionPlanResult(
            work_order_no=work_order.work_order_no,
            product_code=work_order.product_code,
            demand_qty=int(work_order.plan_qty),
            available_minutes=available_minutes,
            target_oee=target_oee,
            total_required_machines=(
                planning_result.total_required_machines
            ),
            estimated_runtime_minutes=(
                planning_result.estimated_runtime_minutes
            ),
            bottleneck_op_code=(
                planning_result.routing_analysis.bottleneck.op_code
            ),
            balance_rows=balance_rows,
            schedule_bookings=schedule_bookings,
            schedule_start=schedule_start,
            schedule_finish=schedule_finish,
            schedule_error=schedule_error,
        )

    # ==========================================================
    # Scheduling (tách riêng để lỗi thiếu máy không làm mất kết quả
    # Capacity/Machine Balance đã tính được ở trên)
    # ==========================================================

    def _try_build_schedule(
        self,
        work_order,
        planning_result,
        resource_pool,
        schedule_start_time,
    ):
        try:
            start_time = (
                schedule_start_time
                or self._default_schedule_start(work_order)
            )

            scheduler_request = SchedulerRequest(
                work_order_code=work_order.work_order_no,
                planning_result=planning_result,
                resource_pool=resource_pool,
                start_time=start_time,
            )

            schedule_result = (
                self.scheduler_engine.create_schedule(
                    scheduler_request
                )
            )

            return (
                list(schedule_result.bookings),
                schedule_result.start_time,
                schedule_result.finish_time,
                None,
            )

        except (SchedulerError, PlanningError) as error:
            # Thiếu máy, resource pool rỗng, v.v. - Capacity/Machine
            # Balance vẫn hữu ích ngay cả khi không lập được lịch.
            return [], None, None, str(error)

    # ==========================================================
    # Mapping: DB Routing row -> planning.models.Operation
    # ==========================================================

    def _map_operation(self, routing_row) -> Operation:
        op_code = f"OP{int(routing_row.operation_no)}"

        machine_group = (
            str(routing_row.machine_type or "OTHER")
            .strip()
            .upper()
            or "OTHER"
        )

        cycle_time_sec = float(
            routing_row.standard_cycle_time_sec or 0
        )

        if cycle_time_sec <= 0:
            raise ValidationError(
                f"Routing {routing_row.product_code} / {op_code} "
                "has invalid Standard Cycle Time (must be greater "
                "than zero) - cannot plan. Please fix the Routing "
                "first."
            )

        employee_required = max(
            1,
            round(
                float(routing_row.standard_operator_count or 1)
            ),
        )

        return Operation(
            op_code=op_code,
            sequence=int(routing_row.operation_no),
            machine_group=machine_group,
            cycle_time_sec=cycle_time_sec,
            setup_time_min=0.0,
            employee_required=employee_required,
            standard_qty=1,
        )

    # ==========================================================
    # Resource pool: số máy thực tế hiện có theo machine_type
    # ==========================================================

    def _build_resource_pool(self, target_oee) -> ResourcePool:
        machines = self.machine_service.get_all_machines()

        counts: dict[str, int] = {}

        for machine in machines:
            status = str(machine.status or "").strip().upper()

            if status not in self.AVAILABLE_MACHINE_STATUSES:
                continue

            group = (
                str(machine.machine_type or "OTHER")
                .strip()
                .upper()
                or "OTHER"
            )

            counts[group] = counts.get(group, 0) + 1

        resources = tuple(
            MachineResource(
                machine_group=group,
                available_machines=count,
                target_oee=target_oee,
            )
            for group, count in counts.items()
        )

        return ResourcePool(resources=resources)

    # ==========================================================
    # Capacity / Machine Balance table rows
    # ==========================================================

    def _build_balance_rows(
        self,
        planning_result,
        demand_qty,
        available_minutes,
        target_oee,
        resource_pool,
    ):
        rows = []

        for operation_plan in planning_result.operation_plans:
            operation = operation_plan.operation

            try:
                required_for_demand = (
                    CapacityEngine
                    .calculate_required_machines_for_demand(
                        demand_qty=demand_qty,
                        cycle_time_sec=operation.cycle_time_sec,
                        available_minutes=available_minutes,
                        target_oee=target_oee,
                    )
                )
            except PlanningError:
                # Không nên xảy ra vì input đã được validate ở trên,
                # nhưng vẫn phòng hờ để không làm hỏng cả bảng.
                required_for_demand = operation_plan.required_machines

            available = resource_pool.find(operation.machine_group)
            available_count = (
                available.available_machines
                if available is not None
                else 0
            )

            shortage = max(
                0,
                operation_plan.required_machines - available_count,
            )

            rows.append(
                MachineBalanceRow(
                    op_code=operation.op_code,
                    sequence=operation.sequence,
                    machine_group=operation.machine_group,
                    cycle_time_sec=operation.cycle_time_sec,
                    required_machines_balance=(
                        operation_plan.required_machines
                    ),
                    utilization_percent=round(
                        operation_plan.utilization * 100,
                        1,
                    ),
                    is_bottleneck=operation_plan.is_bottleneck,
                    required_machines_for_demand=required_for_demand,
                    available_machines=available_count,
                    shortage=shortage,
                )
            )

        rows.sort(key=lambda row: row.sequence)

        return rows

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _default_schedule_start(work_order) -> datetime:
        start_date = work_order.start_date or date.today()

        return datetime.combine(start_date, time(8, 0))
