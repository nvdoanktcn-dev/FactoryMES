import unittest

from src.planning.exceptions import InvalidRoutingError
from src.planning.models import Operation, Routing
from src.planning.routing_validator import (
    RoutingValidator,
)


class TestRoutingValidator(unittest.TestCase):

    def test_valid_routing_passes_validation(self):
        routing = Routing(
            product_code="P001",
            operations=[
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
            ],
        )

        RoutingValidator.validate(routing)

    def test_empty_routing_raises_error(self):
        routing = Routing(
            product_code="P001",
            operations=[],
        )

        with self.assertRaises(InvalidRoutingError):
            RoutingValidator.validate(routing)

    def test_duplicate_sequence_raises_error(self):
        routing = Routing(
            product_code="P001",
            operations=[
                Operation(
                    op_code="OP10",
                    sequence=10,
                    machine_group="CNC",
                    cycle_time_sec=20,
                ),
                Operation(
                    op_code="OP20",
                    sequence=10,
                    machine_group="ROBOT",
                    cycle_time_sec=40,
                ),
            ],
        )

        with self.assertRaisesRegex(
            InvalidRoutingError,
            "Duplicate operation sequence",
        ):
            RoutingValidator.validate(routing)

    def test_duplicate_op_code_raises_error(self):
        routing = Routing(
            product_code="P001",
            operations=[
                Operation(
                    op_code="OP10",
                    sequence=10,
                    machine_group="CNC",
                    cycle_time_sec=20,
                ),
                Operation(
                    op_code="OP10",
                    sequence=20,
                    machine_group="ROBOT",
                    cycle_time_sec=40,
                ),
            ],
        )

        with self.assertRaisesRegex(
            InvalidRoutingError,
            "Duplicate operation code",
        ):
            RoutingValidator.validate(routing)

    def test_zero_cycle_time_raises_error(self):
        routing = Routing(
            product_code="P001",
            operations=[
                Operation(
                    op_code="OP10",
                    sequence=10,
                    machine_group="CNC",
                    cycle_time_sec=0,
                )
            ],
        )

        with self.assertRaisesRegex(
            InvalidRoutingError,
            "cycle_time_sec",
        ):
            RoutingValidator.validate(routing)


if __name__ == "__main__":
    unittest.main()