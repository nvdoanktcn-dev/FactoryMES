import unittest

from src.dto.oee_result import OEEResult
from src.services.oee_calculation_service import (
    OEECalculationService,
)


class TestOEECalculationService(unittest.TestCase):

    def test_availability_normal(self):
        result = (
            OEECalculationService
            .calculate_availability(
                runtime_minutes=420,
                downtime_minutes=60,
            )
        )

        self.assertAlmostEqual(
            result,
            0.875,
            places=6,
        )

    def test_availability_without_downtime(self):
        result = (
            OEECalculationService
            .calculate_availability(
                runtime_minutes=480,
                downtime_minutes=0,
            )
        )

        self.assertEqual(result, 1.0)

    def test_availability_without_planned_time(self):
        result = (
            OEECalculationService
            .calculate_availability(
                runtime_minutes=0,
                downtime_minutes=0,
            )
        )

        self.assertEqual(result, 0.0)

    def test_availability_runtime_zero(self):
        result = (
            OEECalculationService
            .calculate_availability(
                runtime_minutes=0,
                downtime_minutes=60,
            )
        )

        self.assertEqual(result, 0.0)

    def test_availability_negative_runtime_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Runtime Minutes cannot be negative",
        ):
            OEECalculationService.calculate_availability(
                runtime_minutes=-1,
                downtime_minutes=0,
            )

    def test_availability_negative_downtime_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Downtime Minutes cannot be negative",
        ):
            OEECalculationService.calculate_availability(
                runtime_minutes=1,
                downtime_minutes=-1,
            )

    def test_non_finite_values_fail(self):
        with self.assertRaisesRegex(
            ValueError,
            "Invalid Runtime Minutes",
        ):
            OEECalculationService.calculate_availability(
                runtime_minutes=float("nan"),
                downtime_minutes=0,
            )

        with self.assertRaisesRegex(
            ValueError,
            "Invalid Ideal Cycle Time Sec",
        ):
            OEECalculationService.calculate_performance(
                runtime_minutes=1,
                total_qty=1,
                ideal_cycle_time_sec=float("inf"),
            )

    def test_performance_normal(self):
        result = (
            OEECalculationService
            .calculate_performance(
                runtime_minutes=420,
                total_qty=1000,
                ideal_cycle_time_sec=20,
            )
        )

        self.assertAlmostEqual(
            result,
            0.7936507937,
            places=6,
        )

    def test_performance_runtime_zero(self):
        result = (
            OEECalculationService
            .calculate_performance(
                runtime_minutes=0,
                total_qty=100,
                ideal_cycle_time_sec=20,
            )
        )

        self.assertEqual(result, 0.0)

    def test_performance_quantity_zero(self):
        result = (
            OEECalculationService
            .calculate_performance(
                runtime_minutes=420,
                total_qty=0,
                ideal_cycle_time_sec=20,
            )
        )

        self.assertEqual(result, 0.0)

    def test_performance_can_exceed_one(self):
        result = (
            OEECalculationService
            .calculate_performance(
                runtime_minutes=10,
                total_qty=100,
                ideal_cycle_time_sec=10,
            )
        )

        self.assertGreater(result, 1.0)

    def test_performance_cycle_time_zero_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "must be greater than zero",
        ):
            OEECalculationService.calculate_performance(
                runtime_minutes=10,
                total_qty=10,
                ideal_cycle_time_sec=0,
            )

    def test_performance_negative_cycle_time_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "must be greater than zero",
        ):
            OEECalculationService.calculate_performance(
                runtime_minutes=10,
                total_qty=10,
                ideal_cycle_time_sec=-1,
            )

    def test_performance_negative_quantity_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Total Qty cannot be negative",
        ):
            OEECalculationService.calculate_performance(
                runtime_minutes=10,
                total_qty=-1,
                ideal_cycle_time_sec=20,
            )

    def test_quality_normal(self):
        result = (
            OEECalculationService
            .calculate_quality(
                ok_qty=95,
                ng_qty=5,
            )
        )

        self.assertEqual(result, 0.95)

    def test_quality_all_ok(self):
        result = (
            OEECalculationService
            .calculate_quality(
                ok_qty=100,
                ng_qty=0,
            )
        )

        self.assertEqual(result, 1.0)

    def test_quality_all_ng(self):
        result = (
            OEECalculationService
            .calculate_quality(
                ok_qty=0,
                ng_qty=100,
            )
        )

        self.assertEqual(result, 0.0)

    def test_quality_without_production(self):
        result = (
            OEECalculationService
            .calculate_quality(
                ok_qty=0,
                ng_qty=0,
            )
        )

        self.assertEqual(result, 0.0)

    def test_quality_negative_ok_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "OK Qty cannot be negative",
        ):
            OEECalculationService.calculate_quality(
                ok_qty=-1,
                ng_qty=0,
            )

    def test_quality_negative_ng_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "NG Qty cannot be negative",
        ):
            OEECalculationService.calculate_quality(
                ok_qty=0,
                ng_qty=-1,
            )

    def test_calculate_oee_normal(self):
        result = (
            OEECalculationService
            .calculate_oee(
                availability=0.875,
                performance=0.8,
                quality=0.95,
            )
        )

        self.assertAlmostEqual(
            result,
            0.665,
            places=6,
        )

    def test_calculate_oee_zero_component(self):
        result = (
            OEECalculationService
            .calculate_oee(
                availability=0.875,
                performance=0,
                quality=0.95,
            )
        )

        self.assertEqual(result, 0.0)

    def test_calculate_oee_performance_above_one(self):
        result = (
            OEECalculationService
            .calculate_oee(
                availability=1,
                performance=1.2,
                quality=1,
            )
        )

        self.assertEqual(result, 1.2)

    def test_calculate_oee_availability_above_one_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Availability cannot be greater than 1",
        ):
            OEECalculationService.calculate_oee(
                availability=1.1,
                performance=1,
                quality=1,
            )

    def test_calculate_oee_quality_above_one_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "Quality cannot be greater than 1",
        ):
            OEECalculationService.calculate_oee(
                availability=1,
                performance=1,
                quality=1.1,
            )

    def test_calculate_execution_oee_returns_dto(self):
        result = (
            OEECalculationService
            .calculate_execution_oee(
                runtime_minutes=420,
                downtime_minutes=60,
                ok_qty=995,
                ng_qty=5,
                ideal_cycle_time_sec=20,
            )
        )

        self.assertIsInstance(result, OEEResult)
        self.assertEqual(result.runtime_minutes, 420)
        self.assertEqual(result.downtime_minutes, 60)
        self.assertEqual(result.total_qty, 1000)
        self.assertEqual(result.ok_qty, 995)
        self.assertEqual(result.ng_qty, 5)

    def test_calculate_execution_oee_values(self):
        result = (
            OEECalculationService
            .calculate_execution_oee(
                runtime_minutes=420,
                downtime_minutes=60,
                ok_qty=995,
                ng_qty=5,
                ideal_cycle_time_sec=20,
            )
        )

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

        expected_oee = (
            0.875
            * 0.7936507936507936
            * 0.995
        )

        self.assertAlmostEqual(
            result.oee,
            expected_oee,
            places=6,
        )

    def test_oee_result_is_immutable(self):
        result = OEEResult(
            availability=1,
            performance=1,
            quality=1,
            oee=1,
            runtime_minutes=60,
            downtime_minutes=0,
            total_qty=100,
            ok_qty=100,
            ng_qty=0,
        )

        with self.assertRaises(Exception):
            result.oee = 0.5


if __name__ == "__main__":
    unittest.main()
