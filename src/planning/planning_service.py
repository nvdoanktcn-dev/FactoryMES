from __future__ import annotations

from src.planning.capacity_engine import CapacityEngine
from src.planning.models import (
    OperationPlan,
    PlanningRequest,
    PlanningResult,
)
from src.planning.routing_engine import RoutingEngine


class PlanningService:

    def __init__(
        self,
        routing_engine=None,
        capacity_engine=None,
    ):
        self.routing_engine = (
            routing_engine
            or RoutingEngine()
        )

        self.capacity_engine = (
            capacity_engine
            or CapacityEngine()
        )

    def analyze(
        self,
        request: PlanningRequest,
    ) -> PlanningResult:

        routing_analysis = (
            self.routing_engine.analyze(
                routing=request.routing,
                reference_sequence=request.reference_sequence,
            )
        )

        operation_plans = []

        max_runtime = 0.0

        for capacity in routing_analysis.capacities:

            runtime = (
                request.demand_qty
                * capacity.cycle_time_sec
                / capacity.required_machines
                / 60
            )

            max_runtime = max(
                max_runtime,
                runtime,
            )

            operation = next(
                op
                for op in request.routing.operations
                if op.op_code == capacity.op_code
            )

            operation_plans.append(
                OperationPlan(
                    operation=operation,
                    required_machines=capacity.required_machines,
                    estimated_runtime_minutes=runtime,
                    utilization=capacity.utilization,
                    is_bottleneck=capacity.is_bottleneck,
                )
            )

        return PlanningResult(
            request=request,
            routing_analysis=routing_analysis,
            operation_plans=tuple(operation_plans),
            total_required_machines=max(
                p.required_machines
                for p in operation_plans
            ),
            estimated_runtime_minutes=max_runtime,
        )