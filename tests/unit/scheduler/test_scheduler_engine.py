import unittest
from dataclasses import dataclass
from datetime import datetime

from src.planning.models import (
    CapacityResult,
    Operation,
    OperationPlan,
    PlanningRequest,
    PlanningResult,
    Routing,
    RoutingAnalysis,
)
from src.scheduler.exceptions import (
    InsufficientResourceError,
)
from src.scheduler.models import SchedulerRequest
from src.scheduler.scheduler_engine import (
    SchedulerEngine,
)


@dataclass(frozen=True)
class FakeMachineResource:
    machine_group: str
    available_machines: int


class FakeResourcePool:
    def __init__(
        self,
        resources: tuple[FakeMachineResource, ...],
    ) -> None:
        self._resources = {
            resource.machine_group.strip().upper(): resource
            for resource in resources
        }

    def __len__(self) -> int:
        return len(self._resources)

    def get(
        self,
        machine_group: str,
    ) -> FakeMachineResource:
        normalized_group = (
            machine_group.strip().upper()
        )

        if normalized_group not in self._resources:
            raise KeyError(normalized_group)

        return self._resources[normalized_group]


class TestSchedulerEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = SchedulerEngine()

        self.start_time = datetime(
            2026,
            7,
            20,
            8,
            0,
        )

    @staticmethod
    def create_operation(
        op_code: str = "OP10",
        sequence: int = 10,
        machine_group: str = "CNC",
        cycle_time_sec: float = 20.0,
    ) -> Operation:
        return Operation(
            op_code=op_code,
            sequence=sequence,
            machine_group=machine_group,
            cycle_time_sec=cycle_time_sec,
        )

    def create_planning_result(
        self,
        operations: tuple[Operation, ...],
        required_machines: tuple[int, ...],
        runtimes: tuple[float, ...],
        demand_qty: int = 100,
    ) -> PlanningResult:
        routing = Routing(
            product_code="P-001",
            operations=operations,
        )

        capacities = tuple(
            CapacityResult(
                op_code=operation.op_code,
                sequence=operation.sequence,
                machine_group=operation.machine_group,
                cycle_time_sec=operation.cycle_time_sec,
                reference_cycle_time_sec=(
                    operations[0].cycle_time_sec
                ),
                required_machines=machine_count,
                utilization=1.0,
                is_bottleneck=False,
            )
            for operation, machine_count in zip(
                operations,
                required_machines,
            )
        )

        bottleneck = max(
            operations,
            key=lambda operation: (
                operation.cycle_time_sec,
                -operation.sequence,
            ),
        )

        routing_analysis = RoutingAnalysis(
            product_code=routing.product_code,
            capacities=capacities,
            bottleneck=bottleneck,
        )

        planning_request = PlanningRequest(
            routing=routing,
            demand_qty=demand_qty,
            available_minutes=480.0,
            target_oee=0.85,
        )

        operation_plans = tuple(
            OperationPlan(
                operation=operation,
                required_machines=machine_count,
                estimated_runtime_minutes=runtime,
                utilization=1.0,
                is_bottleneck=(
                    operation.op_code
                    == bottleneck.op_code
                ),
            )
            for operation, machine_count, runtime in zip(
                operations,
                required_machines,
                runtimes,
            )
        )

        return PlanningResult(
            request=planning_request,
            routing_analysis=routing_analysis,
            operation_plans=operation_plans,
            total_required_machines=sum(
                required_machines
            ),
            estimated_runtime_minutes=sum(runtimes),
        )

    def create_request(
        self,
        planning_result: PlanningResult,
        resources: tuple[FakeMachineResource, ...],
    ) -> SchedulerRequest:
        return SchedulerRequest(
            work_order_code="WO-001",
            planning_result=planning_result,
            resource_pool=FakeResourcePool(resources),
            start_time=self.start_time,
        )

    def test_create_schedule_with_one_operation(
        self,
    ) -> None:
        operation = self.create_operation()

        planning_result = self.create_planning_result(
            operations=(operation,),
            required_machines=(1,),
            runtimes=(60.0,),
        )

        request = self.create_request(
            planning_result,
            resources=(
                FakeMachineResource(
                    machine_group="CNC",
                    available_machines=2,
                ),
            ),
        )

        result = self.engine.create_schedule(request)

        self.assertEqual(result.total_bookings, 1)
        self.assertEqual(
            result.bookings[0].machine_code,
            "CNC01",
        )
        self.assertEqual(
            result.bookings[0].op_code,
            "OP10",
        )
        self.assertEqual(
            result.bookings[0].duration_minutes,
            60.0,
        )

    def test_booking_quantity_equals_demand(
        self,
    ) -> None:
        operation = self.create_operation()

        planning_result = self.create_planning_result(
            operations=(operation,),
            required_machines=(1,),
            runtimes=(30.0,),
            demand_qty=120,
        )

        request = self.create_request(
            planning_result,
            resources=(
                FakeMachineResource("CNC", 1),
            ),
        )

        result = self.engine.create_schedule(request)

        self.assertEqual(
            result.bookings[0].quantity,
            120,
        )

    def test_multiple_operations_are_sequential(
        self,
    ) -> None:
        op10 = self.create_operation(
            op_code="OP10",
            sequence=10,
            machine_group="CNC",
            cycle_time_sec=20.0,
        )

        op20 = self.create_operation(
            op_code="OP20",
            sequence=20,
            machine_group="ROBOT",
            cycle_time_sec=40.0,
        )

        planning_result = self.create_planning_result(
            operations=(op10, op20),
            required_machines=(1, 1),
            runtimes=(30.0, 45.0),
        )

        request = self.create_request(
            planning_result,
            resources=(
                FakeMachineResource("CNC", 2),
                FakeMachineResource("ROBOT", 2),
            ),
        )

        result = self.engine.create_schedule(request)

        self.assertEqual(result.total_bookings, 2)

        first_booking = result.bookings[0]
        second_booking = result.bookings[1]

        self.assertEqual(
            first_booking.end_time,
            second_booking.start_time,
        )
        self.assertEqual(
            result.finish_time,
            second_booking.end_time,
        )

    def test_operations_are_sorted_by_sequence(
        self,
    ) -> None:
        op20 = self.create_operation(
            op_code="OP20",
            sequence=20,
            machine_group="ROBOT",
        )

        op10 = self.create_operation(
            op_code="OP10",
            sequence=10,
            machine_group="CNC",
        )

        planning_result = self.create_planning_result(
            operations=(op20, op10),
            required_machines=(1, 1),
            runtimes=(40.0, 20.0),
        )

        request = self.create_request(
            planning_result,
            resources=(
                FakeMachineResource("CNC", 1),
                FakeMachineResource("ROBOT", 1),
            ),
        )

        result = self.engine.create_schedule(request)

        self.assertEqual(
            result.bookings[0].op_code,
            "OP10",
        )
        self.assertEqual(
            result.bookings[1].op_code,
            "OP20",
        )

    def test_parallel_machines_create_parallel_bookings(
        self,
    ) -> None:
        operation = self.create_operation()

        planning_result = self.create_planning_result(
            operations=(operation,),
            required_machines=(2,),
            runtimes=(60.0,),
            demand_qty=100,
        )

        request = self.create_request(
            planning_result,
            resources=(
                FakeMachineResource("CNC", 3),
            ),
        )

        result = self.engine.create_schedule(request)

        self.assertEqual(result.total_bookings, 2)

        first_booking = result.bookings[0]
        second_booking = result.bookings[1]

        self.assertEqual(
            first_booking.start_time,
            second_booking.start_time,
        )
        self.assertEqual(
            first_booking.end_time,
            second_booking.end_time,
        )
        self.assertEqual(
            first_booking.machine_code,
            "CNC01",
        )
        self.assertEqual(
            second_booking.machine_code,
            "CNC02",
        )

    def test_quantity_is_distributed_between_machines(
        self,
    ) -> None:
        operation = self.create_operation()

        planning_result = self.create_planning_result(
            operations=(operation,),
            required_machines=(3,),
            runtimes=(60.0,),
            demand_qty=100,
        )

        request = self.create_request(
            planning_result,
            resources=(
                FakeMachineResource("CNC", 3),
            ),
        )

        result = self.engine.create_schedule(request)

        quantities = tuple(
            booking.quantity
            for booking in result.bookings
        )

        self.assertEqual(
            quantities,
            (34, 33, 33),
        )
        self.assertEqual(sum(quantities), 100)

    def test_insufficient_resources_raises_error(
        self,
    ) -> None:
        operation = self.create_operation()

        planning_result = self.create_planning_result(
            operations=(operation,),
            required_machines=(3,),
            runtimes=(60.0,),
        )

        request = self.create_request(
            planning_result,
            resources=(
                FakeMachineResource("CNC", 2),
            ),
        )

        with self.assertRaises(
            InsufficientResourceError
        ):
            self.engine.create_schedule(request)

    def test_missing_machine_group_raises_error(
        self,
    ) -> None:
        operation = self.create_operation(
            machine_group="ROBOT",
        )

        planning_result = self.create_planning_result(
            operations=(operation,),
            required_machines=(1,),
            runtimes=(60.0,),
        )

        request = self.create_request(
            planning_result,
            resources=(
                FakeMachineResource("CNC", 2),
            ),
        )

        with self.assertRaises(
            InsufficientResourceError
        ):
            self.engine.create_schedule(request)

    def test_finish_time_matches_last_booking(
        self,
    ) -> None:
        operation = self.create_operation()

        planning_result = self.create_planning_result(
            operations=(operation,),
            required_machines=(2,),
            runtimes=(90.0,),
        )

        request = self.create_request(
            planning_result,
            resources=(
                FakeMachineResource("CNC", 2),
            ),
        )

        result = self.engine.create_schedule(request)

        self.assertEqual(
            result.finish_time,
            result.bookings[-1].end_time,
        )


if __name__ == "__main__":
    unittest.main()