import unittest

from src.planning.capacity_engine import CapacityEngine
from src.planning.exceptions import (
    InvalidCapacityInputError,
)


class TestCapacityEngine(unittest.TestCase):

    def test_equal_cycle_requires_one_machine(self):
        result = (
            CapacityEngine
            .calculate_required_machines(
                reference_cycle_time_sec=20,
                current_cycle_time_sec=20,
            )
        )

        self.assertEqual(result, 1)

    def test_double_cycle_requires_two_machines(self):
        result = (
            CapacityEngine
            .calculate_required_machines(
                reference_cycle_time_sec=20,
                current_cycle_time_sec=40,
            )
        )

        self.assertEqual(result, 2)

    def test_quad_cycle_requires_four_machines(self):
        result = (
            CapacityEngine
            .calculate_required_machines(
                reference_cycle_time_sec=80,
                current_cycle_time_sec=320,
            )
        )

        self.assertEqual(result, 4)

    def test_fractional_ratio_rounds_up(self):
        result = (
            CapacityEngine
            .calculate_required_machines(
                reference_cycle_time_sec=20,
                current_cycle_time_sec=45,
            )
        )

        self.assertEqual(result, 3)

    def test_two_balanced_machines_have_full_utilization(self):
        utilization = (
            CapacityEngine
            .calculate_utilization(
                reference_cycle_time_sec=20,
                current_cycle_time_sec=40,
                machine_count=2,
            )
        )

        self.assertAlmostEqual(
            utilization,
            1.0,
        )

    def test_effective_cycle_time_uses_parallel_machines(self):
        effective_cycle = (
            CapacityEngine
            .calculate_effective_cycle_time(
                cycle_time_sec=320,
                machine_count=4,
            )
        )

        self.assertEqual(
            effective_cycle,
            80,
        )

    def test_calculate_machines_for_demand(self):
        result = (
            CapacityEngine
            .calculate_required_machines_for_demand(
                demand_qty=1_000,
                cycle_time_sec=30,
                available_minutes=600,
                target_oee=0.85,
            )
        )

        self.assertEqual(result, 1)

    def test_high_demand_requires_multiple_machines(self):
        result = (
            CapacityEngine
            .calculate_required_machines_for_demand(
                demand_qty=3_000,
                cycle_time_sec=30,
                available_minutes=600,
                target_oee=0.85,
            )
        )

        self.assertEqual(result, 3)

    def test_zero_reference_cycle_raises_error(self):
        with self.assertRaises(
            InvalidCapacityInputError
        ):
            (
                CapacityEngine
                .calculate_required_machines(
                    reference_cycle_time_sec=0,
                    current_cycle_time_sec=40,
                )
            )

    def test_target_oee_greater_than_one_raises_error(self):
        with self.assertRaises(
            InvalidCapacityInputError
        ):
            (
                CapacityEngine
                .calculate_required_machines_for_demand(
                    demand_qty=100,
                    cycle_time_sec=30,
                    available_minutes=600,
                    target_oee=1.2,
                )
            )


if __name__ == "__main__":
    unittest.main()