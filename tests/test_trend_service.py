from __future__ import annotations

import unittest
from datetime import datetime

from src.services.trend_service import (
    TrendGranularity,
    TrendService,
)


class TestTrendService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = TrendService()

        self.rows = [
            {
                "started_at": datetime(
                    2026, 7, 20, 8, 30
                ),
                "oee": 80,
                "availability": 90,
                "performance": 90,
                "quality": 98,
                "runtime_minutes": 100,
                "downtime_minutes": 20,
                "ok_qty": 95,
                "ng_qty": 5,
            },
            {
                "started_at": datetime(
                    2026, 7, 20, 15, 30
                ),
                "oee": 60,
                "availability": 70,
                "performance": 80,
                "quality": 95,
                "runtime_minutes": 50,
                "downtime_minutes": 30,
                "ok_qty": 45,
                "ng_qty": 5,
            },
            {
                "started_at": datetime(
                    2026, 7, 21, 8, 0
                ),
                "oee": 90,
                "availability": 95,
                "performance": 96,
                "quality": 99,
                "runtime_minutes": 120,
                "downtime_minutes": 10,
                "ok_qty": 118,
                "ng_qty": 2,
            },
        ]

    def test_empty_rows(self) -> None:
        result = self.service.build([])

        self.assertEqual(result, [])

    def test_daily_grouping(self) -> None:
        result = self.service.build(
            self.rows,
            granularity=TrendGranularity.DAILY,
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result[0].label,
            "20/07/2026",
        )
        self.assertEqual(
            result[1].label,
            "21/07/2026",
        )

    def test_daily_quantity_total(self) -> None:
        result = self.service.build(
            self.rows,
            granularity="daily",
        )

        first_day = result[0]

        self.assertEqual(first_day.ok_qty, 140)
        self.assertEqual(first_day.ng_qty, 10)
        self.assertEqual(
            first_day.runtime_minutes,
            150,
        )
        self.assertEqual(
            first_day.downtime_minutes,
            50,
        )
        self.assertEqual(
            first_day.execution_count,
            2,
        )

    def test_oee_is_weighted_by_runtime(self) -> None:
        result = self.service.build(
            self.rows,
            granularity="daily",
        )

        expected = (
            (80 * 100) + (60 * 50)
        ) / 150

        self.assertAlmostEqual(
            result[0].oee,
            expected,
            places=4,
        )

    def test_hourly_grouping(self) -> None:
        result = self.service.build(
            self.rows,
            granularity="hourly",
        )

        self.assertEqual(len(result), 3)
        self.assertEqual(
            result[0].label,
            "20/07/2026 08:00",
        )

    def test_monthly_grouping(self) -> None:
        result = self.service.build(
            self.rows,
            granularity="monthly",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0].label,
            "07/2026",
        )
        self.assertEqual(
            result[0].execution_count,
            3,
        )

    def test_yearly_grouping(self) -> None:
        result = self.service.build(
            self.rows,
            granularity="yearly",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].label, "2026")

    def test_weekly_grouping(self) -> None:
        result = self.service.build(
            self.rows,
            granularity="weekly",
        )

        self.assertEqual(len(result), 1)
        self.assertTrue(
            result[0].label.startswith("Tuần ")
        )

    def test_custom_datetime_field(self) -> None:
        rows = [
            {
                "production_time": "2026-07-22 09:30",
                "oee": 75,
            }
        ]

        result = self.service.build(
            rows,
            datetime_field="production_time",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0].label,
            "22/07/2026",
        )

    def test_invalid_datetime_is_skipped(self) -> None:
        result = self.service.build(
            [
                {
                    "started_at": "invalid-date",
                    "oee": 80,
                }
            ]
        )

        self.assertEqual(result, [])

    def test_night_shift_after_midnight_uses_shift_date(
        self,
    ) -> None:
        result = self.service.build(
            [
                {
                    "started_at": datetime(
                        2026, 7, 21, 1, 0
                    ),
                    "shift": "NIGHT",
                    "oee": 80,
                }
            ]
        )

        self.assertEqual(
            result[0].label,
            "20/07/2026",
        )

    def test_final_operation_output_is_not_double_counted(
        self,
    ) -> None:
        result = self.service.build(
            [
                {
                    "started_at": datetime(2026, 7, 20, 8),
                    "work_order": "WO-001",
                    "product": "P-001",
                    "op_no": "OP1",
                    "runtime_minutes": 100,
                    "ok_qty": 95,
                    "ng_qty": 5,
                    "quality": 95,
                },
                {
                    "started_at": datetime(2026, 7, 20, 10),
                    "work_order": "WO-001",
                    "product": "P-001",
                    "op_no": "OP2",
                    "runtime_minutes": 120,
                    "ok_qty": 79,
                    "ng_qty": 1,
                    "quality": 98.75,
                },
            ]
        )[0]

        self.assertEqual(result.runtime_minutes, 220)
        self.assertEqual(result.ok_qty, 79)
        self.assertEqual(result.ng_qty, 1)
        self.assertEqual(result.quality, 98.75)

    def test_final_operation_is_selected_across_days(
        self,
    ) -> None:
        result = self.service.build(
            [
                {
                    "started_at": datetime(2026, 7, 20, 8),
                    "work_order": "WO-002",
                    "product": "P-002",
                    "op_no": "OP1",
                    "runtime_minutes": 100,
                    "ok_qty": 95,
                    "ng_qty": 5,
                },
                {
                    "started_at": datetime(2026, 7, 21, 8),
                    "work_order": "WO-002",
                    "product": "P-002",
                    "op_no": "OP2",
                    "runtime_minutes": 120,
                    "ok_qty": 79,
                    "ng_qty": 1,
                },
            ],
            granularity="daily",
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].runtime_minutes, 100)
        self.assertEqual(result[0].ok_qty, 0)
        self.assertEqual(result[0].ng_qty, 0)
        self.assertEqual(result[1].ok_qty, 79)
        self.assertEqual(result[1].ng_qty, 1)

    def test_non_finite_numbers_are_zero(self) -> None:
        result = self.service.build(
            [
                {
                    "started_at": datetime(2026, 7, 20, 8),
                    "runtime_minutes": float("nan"),
                    "downtime_minutes": float("inf"),
                    "ok_qty": float("nan"),
                }
            ]
        )[0]

        self.assertEqual(result.runtime_minutes, 0)
        self.assertEqual(result.downtime_minutes, 0)
        self.assertEqual(result.ok_qty, 0)

    def test_invalid_granularity(self) -> None:
        with self.assertRaises(ValueError):
            self.service.build(
                self.rows,
                granularity="quarterly",
            )


if __name__ == "__main__":
    unittest.main()
