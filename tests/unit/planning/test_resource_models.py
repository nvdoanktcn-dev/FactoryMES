import unittest

from src.planning import (
    InvalidResourceError,
    MachineResource,
    ResourceNotFoundError,
    ResourcePool,
)


class TestMachineResource(unittest.TestCase):

    def test_create_machine_resource(self):
        resource = MachineResource(
            machine_group="CNC",
            available_machines=6,
        )

        self.assertEqual(
            resource.machine_group,
            "CNC",
        )
        self.assertEqual(
            resource.available_machines,
            6,
        )
        self.assertAlmostEqual(
            resource.target_oee,
            0.85,
        )
        self.assertAlmostEqual(
            resource.efficiency,
            1.0,
        )

    def test_machine_group_is_normalized(self):
        resource = MachineResource(
            machine_group="  robot ",
            available_machines=4,
        )

        self.assertEqual(
            resource.machine_group,
            "ROBOT",
        )

    def test_empty_machine_group_raises_error(self):
        with self.assertRaises(
            InvalidResourceError
        ):
            MachineResource(
                machine_group=" ",
                available_machines=1,
            )

    def test_zero_available_machines_raises_error(self):
        with self.assertRaises(
            InvalidResourceError
        ):
            MachineResource(
                machine_group="CNC",
                available_machines=0,
            )

    def test_invalid_target_oee_raises_error(self):
        with self.assertRaises(
            InvalidResourceError
        ):
            MachineResource(
                machine_group="CNC",
                available_machines=5,
                target_oee=1.1,
            )

    def test_invalid_efficiency_raises_error(self):
        with self.assertRaises(
            InvalidResourceError
        ):
            MachineResource(
                machine_group="CNC",
                available_machines=5,
                efficiency=0,
            )


class TestResourcePool(unittest.TestCase):

    def setUp(self):
        self.pool = ResourcePool(
            resources=(
                MachineResource(
                    machine_group="CNC",
                    available_machines=6,
                ),
                MachineResource(
                    machine_group="ROBOT",
                    available_machines=4,
                ),
                MachineResource(
                    machine_group="ASK",
                    available_machines=2,
                ),
            )
        )

    def test_get_existing_resource(self):
        resource = self.pool.get("CNC")

        self.assertEqual(
            resource.available_machines,
            6,
        )

    def test_get_is_case_insensitive(self):
        resource = self.pool.get(" robot ")

        self.assertEqual(
            resource.machine_group,
            "ROBOT",
        )

    def test_missing_resource_raises_error(self):
        with self.assertRaises(
            ResourceNotFoundError
        ):
            self.pool.get("MILLING")

    def test_find_missing_resource_returns_none(self):
        self.assertIsNone(
            self.pool.find("MILLING")
        )

    def test_contains_resource(self):
        self.assertTrue(
            self.pool.contains("ASK")
        )
        self.assertFalse(
            self.pool.contains("UNKNOWN")
        )

    def test_available_count(self):
        self.assertEqual(
            self.pool.available_count("ROBOT"),
            4,
        )

    def test_duplicate_machine_group_raises_error(self):
        with self.assertRaises(
            InvalidResourceError
        ):
            ResourcePool(
                resources=(
                    MachineResource(
                        machine_group="cnc",
                        available_machines=5,
                    ),
                    MachineResource(
                        machine_group="CNC",
                        available_machines=3,
                    ),
                )
            )

    def test_evaluate_gap_when_resource_is_sufficient(self):
        gap = self.pool.evaluate_gap(
            machine_group="CNC",
            required=4,
        )

        self.assertEqual(
            gap.required,
            4,
        )
        self.assertEqual(
            gap.available,
            6,
        )
        self.assertEqual(
            gap.shortage,
            0,
        )
        self.assertFalse(
            gap.has_shortage
        )

    def test_evaluate_gap_when_resource_is_insufficient(self):
        gap = self.pool.evaluate_gap(
            machine_group="ROBOT",
            required=7,
        )

        self.assertEqual(
            gap.required,
            7,
        )
        self.assertEqual(
            gap.available,
            4,
        )
        self.assertEqual(
            gap.shortage,
            3,
        )
        self.assertTrue(
            gap.has_shortage
        )

    def test_resource_pool_length(self):
        self.assertEqual(
            len(self.pool),
            3,
        )

    def test_resource_pool_iteration(self):
        groups = [
            resource.machine_group
            for resource in self.pool
        ]

        self.assertEqual(
            groups,
            ["CNC", "ROBOT", "ASK"],
        )


if __name__ == "__main__":
    unittest.main()