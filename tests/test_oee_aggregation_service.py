import unittest
from types import SimpleNamespace

from src.dto.oee_result import OEEResult
from src.services.oee_aggregation_service import (
    OEEAggregationRow,
    OEEAggregationService,
)


class TestOEEAggregationService(
    unittest.TestCase
):

    def test_empty_rows_returns_zero_result(self):
        result = (
            OEEAggregationService.aggregate([])
        )

        self.assertEqual(
            result,
            OEEAggregationService.empty_result(),
        )

    def test_single_row(self):
        result = OEEAggregationService.aggregate(
            [
                OEEAggregationRow(
                    runtime_minutes=420,
                    downtime_minutes=60,
                    ok_qty=995,
                    ng_qty=5,
                    cycle_time_sec=20,
                )
            ]
        )

        self.assertIsInstance(result, OEEResult)
        self.assertAlmostEqual(
            result.availability,
            0.875,
            places=6,
        )
        self.assertAlmostEqual(
            result.performance,
            0.7936507937,
            places=6,
        )
        self.assertAlmostEqual(
            result.quality,
            0.995,
            places=6,
        )
        self.assertAlmostEqual(
            result.oee,
            0.6909722222,
            places=6,
        )

    def test_multiple_rows_same_cycle_time(self):
        result = OEEAggregationService.aggregate(
            [
                OEEAggregationRow(
                    210, 30, 495, 5, 20
                ),
                OEEAggregationRow(
                    210, 30, 500, 0, 20
                ),
            ]
        )

        self.assertEqual(result.runtime_minutes, 420)
        self.assertEqual(result.downtime_minutes, 60)
        self.assertEqual(result.total_qty, 1000)
        self.assertEqual(result.ok_qty, 995)
        self.assertEqual(result.ng_qty, 5)
        self.assertAlmostEqual(
            result.performance,
            0.7936507937,
            places=6,
        )

    def test_mixed_cycle_times_are_weighted(self):
        result = OEEAggregationService.aggregate(
            [
                OEEAggregationRow(
                    100, 20, 100, 0, 30
                ),
                OEEAggregationRow(
                    100, 20, 100, 0, 60
                ),
            ]
        )

        # Weighted cycle = 45 seconds.
        # Ideal runtime = 45 * 200 / 60 = 150 minutes.
        # Performance = 150 / 200 = 0.75.
        self.assertAlmostEqual(
            result.performance,
            0.75,
            places=6,
        )

    def test_mixed_cycle_times_preserve_total_oee(self):
        result = OEEAggregationService.aggregate(
            [
                OEEAggregationRow(
                    100, 20, 90, 10, 30
                ),
                OEEAggregationRow(
                    100, 20, 100, 0, 60
                ),
            ]
        )

        self.assertAlmostEqual(
            result.availability,
            200 / 240,
            places=6,
        )
        self.assertAlmostEqual(
            result.performance,
            0.75,
            places=6,
        )
        self.assertAlmostEqual(
            result.quality,
            0.95,
            places=6,
        )
        self.assertAlmostEqual(
            result.oee,
            (200 / 240) * 0.75 * 0.95,
            places=6,
        )

    def test_route_metadata_counts_only_highest_operation(self):
        result = OEEAggregationService.aggregate(
            [
                OEEAggregationRow(
                    100, 20, 90, 10, 30,
                    "WO-001", "P-001", 1,
                ),
                OEEAggregationRow(
                    120, 30, 79, 1, 60,
                    "WO-001", "P-001", 2,
                ),
            ]
        )

        self.assertEqual(result.runtime_minutes, 220)
        self.assertEqual(result.downtime_minutes, 50)
        self.assertEqual(result.total_qty, 80)
        self.assertEqual(result.ok_qty, 79)
        self.assertEqual(result.ng_qty, 1)

    def test_explicit_non_final_row_keeps_time_only(self):
        result = OEEAggregationService.aggregate(
            [
                OEEAggregationRow(
                    60, 10, 100, 0, 30,
                    "WO-001", "P-001", 1, False,
                )
            ]
        )

        self.assertEqual(result.runtime_minutes, 60)
        self.assertEqual(result.downtime_minutes, 10)
        self.assertEqual(result.total_qty, 0)
        self.assertAlmostEqual(
            result.availability,
            60 / 70,
            places=6,
        )

    def test_dictionary_rows_are_supported(self):
        result = OEEAggregationService.aggregate(
            [
                {
                    "runtime_minutes": 60,
                    "downtime_minutes": 0,
                    "ok_qty": 60,
                    "ng_qty": 0,
                    "cycle_time_sec": 60,
                }
            ]
        )

        self.assertEqual(result.oee, 1.0)

    def test_attribute_rows_are_supported(self):
        row = SimpleNamespace(
            runtime_minutes=60,
            downtime_minutes=0,
            ok_qty=60,
            ng_qty=0,
            cycle_time_sec=60,
        )

        result = OEEAggregationService.aggregate(
            [row]
        )

        self.assertEqual(result.oee, 1.0)

    def test_zero_quantity_keeps_availability(self):
        result = OEEAggregationService.aggregate(
            [
                OEEAggregationRow(
                    runtime_minutes=60,
                    downtime_minutes=20,
                    ok_qty=0,
                    ng_qty=0,
                    cycle_time_sec=30,
                )
            ]
        )

        self.assertEqual(result.availability, 0.75)
        self.assertEqual(result.performance, 0.0)
        self.assertEqual(result.quality, 0.0)
        self.assertEqual(result.oee, 0.0)

    def test_zero_runtime_with_quantity(self):
        result = OEEAggregationService.aggregate(
            [
                OEEAggregationRow(
                    runtime_minutes=0,
                    downtime_minutes=60,
                    ok_qty=10,
                    ng_qty=0,
                    cycle_time_sec=30,
                )
            ]
        )

        self.assertEqual(result.availability, 0.0)
        self.assertEqual(result.performance, 0.0)
        self.assertEqual(result.oee, 0.0)

    def test_performance_can_exceed_one(self):
        result = OEEAggregationService.aggregate(
            [
                OEEAggregationRow(
                    runtime_minutes=10,
                    downtime_minutes=0,
                    ok_qty=100,
                    ng_qty=0,
                    cycle_time_sec=10,
                )
            ]
        )

        self.assertGreater(result.performance, 1.0)
        self.assertGreater(result.oee, 1.0)

    def test_negative_runtime_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Runtime Minutes cannot be negative",
        ):
            OEEAggregationService.aggregate(
                [OEEAggregationRow(-1, 0, 0, 0, 10)]
            )

    def test_negative_downtime_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Downtime Minutes cannot be negative",
        ):
            OEEAggregationService.aggregate(
                [OEEAggregationRow(1, -1, 0, 0, 10)]
            )

    def test_negative_ok_qty_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "OK Qty cannot be negative",
        ):
            OEEAggregationService.aggregate(
                [OEEAggregationRow(1, 0, -1, 0, 10)]
            )

    def test_negative_ng_qty_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "NG Qty cannot be negative",
        ):
            OEEAggregationService.aggregate(
                [OEEAggregationRow(1, 0, 0, -1, 10)]
            )

    def test_zero_cycle_time_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Cycle Time Sec must be greater than zero",
        ):
            OEEAggregationService.aggregate(
                [OEEAggregationRow(1, 0, 1, 0, 0)]
            )

    def test_negative_cycle_time_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Cycle Time Sec must be greater than zero",
        ):
            OEEAggregationService.aggregate(
                [OEEAggregationRow(1, 0, 1, 0, -1)]
            )

    def test_invalid_cycle_time_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Invalid Cycle Time Sec",
        ):
            OEEAggregationService.aggregate(
                [
                    {
                        "runtime_minutes": 1,
                        "downtime_minutes": 0,
                        "ok_qty": 1,
                        "ng_qty": 0,
                        "cycle_time_sec": "invalid",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
