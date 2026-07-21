import unittest

from src.planning.models import Operation, Routing
from src.planning.routing_engine import RoutingEngine


class TestRoutingEngine(unittest.TestCase):

    def setUp(self):
        self.engine = RoutingEngine()

    @staticmethod
    def create_routing() -> Routing:
        return Routing(
            product_code="P001",
            operations=[
                Operation(
                    op_code="OP30",
                    sequence=30,
                    machine_group="ROBOT",
                    cycle_time_sec=90,
                ),
                Operation(
                    op_code="OP10",
                    sequence=10,
                    machine_group="CNC",
                    cycle_time_sec=20,
                ),
                Operation(
                    op_code="OP20",
                    sequence=20,
                    machine_group="CNC",
                    cycle_time_sec=40,
                ),
                Operation(
                    op_code="OP40",
                    sequence=40,
                    machine_group="ROBOT",
                    cycle_time_sec=18,
                ),
            ],
        )

    def test_find_bottleneck_returns_longest_cycle(self):
        routing = self.create_routing()

        bottleneck = self.engine.find_bottleneck(
            routing
        )

        self.assertEqual(
            bottleneck.op_code,
            "OP30",
        )
        self.assertEqual(
            bottleneck.cycle_time_sec,
            90,
        )

    def test_capacity_profile_is_sorted_by_sequence(self):
        routing = self.create_routing()

        profile = (
            self.engine
            .build_capacity_profile(routing)
        )

        self.assertEqual(
            [
                item.op_code
                for item in profile
            ],
            [
                "OP10",
                "OP20",
                "OP30",
                "OP40",
            ],
        )

    def test_capacity_profile_calculates_required_machines(self):
        routing = self.create_routing()

        profile = (
            self.engine
            .build_capacity_profile(routing)
        )

        result_by_op = {
            item.op_code: item
            for item in profile
        }

        self.assertEqual(
            result_by_op["OP10"].required_machines,
            1,
        )
        self.assertEqual(
            result_by_op["OP20"].required_machines,
            2,
        )
        self.assertEqual(
            result_by_op["OP30"].required_machines,
            5,
        )
        self.assertEqual(
            result_by_op["OP40"].required_machines,
            1,
        )

    def test_capacity_profile_marks_bottleneck(self):
        routing = self.create_routing()

        profile = (
            self.engine
            .build_capacity_profile(routing)
        )

        bottlenecks = [
            item.op_code
            for item in profile
            if item.is_bottleneck
        ]

        self.assertEqual(
            bottlenecks,
            ["OP30"],
        )

    def test_custom_reference_operation(self):
        routing = Routing(
            product_code="P002",
            operations=[
                Operation(
                    op_code="OP10",
                    sequence=10,
                    machine_group="CNC",
                    cycle_time_sec=80,
                ),
                Operation(
                    op_code="OP20",
                    sequence=20,
                    machine_group="ROBOT",
                    cycle_time_sec=320,
                ),
            ],
        )

        profile = (
            self.engine
            .build_capacity_profile(
                routing,
                reference_sequence=10,
            )
        )

        self.assertEqual(
            profile[1].required_machines,
            4,
        )

    def test_analyze_returns_complete_result(self):
        routing = self.create_routing()

        result = self.engine.analyze(routing)

        self.assertEqual(
            result.product_code,
            "P001",
        )
        self.assertEqual(
            result.total_operations,
            4,
        )
        self.assertEqual(
            result.maximum_required_machines,
            5,
        )
        self.assertEqual(
            result.bottleneck.op_code,
            "OP30",
        )


if __name__ == "__main__":
    unittest.main()