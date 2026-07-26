from __future__ import annotations

import unittest
from dataclasses import dataclass

from src.services.progress_service import (
    ProgressService,
    ProgressStatus,
)


@dataclass
class ProgressRow:
    work_order: str
    product: str
    planned_qty: int
    completed_qty: int


class TestProgressService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ProgressService()

    def test_empty_rows(self) -> None:
        self.assertEqual(
            self.service.build([]),
            [],
        )

    def test_build_single_item(self) -> None:
        result = self.service.build(
            [
                {
                    "work_order": "WO001",
                    "product": "P001",
                    "planned_qty": 1000,
                    "completed_qty": 500,
                }
            ]
        )

        self.assertEqual(len(result), 1)

        item = result[0]

        self.assertEqual(
            item.work_order,
            "WO001",
        )
        self.assertEqual(
            item.product,
            "P001",
        )

    def test_progress_calculation(self) -> None:
        item = self.service.build_one(
            {
                "work_order": "WO001",
                "planned_qty": 1000,
                "completed_qty": 725,
            }
        )

        self.assertIsNotNone(item)
        self.assertEqual(
            item.progress_percent,
            72.5,
        )
        self.assertEqual(
            item.remaining_qty,
            275,
        )

    def test_completed_status(self) -> None:
        item = self.service.build_one(
            {
                "work_order": "WO001",
                "planned_qty": 100,
                "completed_qty": 100,
            }
        )

        self.assertEqual(
            item.status,
            ProgressStatus.COMPLETED,
        )
        self.assertEqual(
            item.remaining_qty,
            0,
        )

    def test_over_completed_status(self) -> None:
        item = self.service.build_one(
            {
                "work_order": "WO001",
                "planned_qty": 100,
                "completed_qty": 120,
            }
        )

        self.assertEqual(
            item.status,
            ProgressStatus.OVER_COMPLETED,
        )
        self.assertEqual(
            item.progress_percent,
            120.0,
        )
        self.assertEqual(
            item.display_percent,
            100.0,
        )
        self.assertEqual(
            item.over_completed_qty,
            20,
        )

    def test_on_track_status(self) -> None:
        item = self.service.build_one(
            {
                "work_order": "WO001",
                "planned_qty": 100,
                "completed_qty": 85,
            }
        )

        self.assertEqual(
            item.status,
            ProgressStatus.ON_TRACK,
        )

    def test_in_progress_status(self) -> None:
        item = self.service.build_one(
            {
                "work_order": "WO001",
                "planned_qty": 100,
                "completed_qty": 40,
            }
        )

        self.assertEqual(
            item.status,
            ProgressStatus.IN_PROGRESS,
        )

    def test_not_started_status(self) -> None:
        item = self.service.build_one(
            {
                "work_order": "WO001",
                "planned_qty": 100,
                "completed_qty": 0,
            }
        )

        self.assertEqual(
            item.status,
            ProgressStatus.NOT_STARTED,
        )

    def test_duplicate_work_order_is_aggregated(
        self,
    ) -> None:
        result = self.service.build(
            [
                {
                    "work_order": "WO001",
                    "product": "P001",
                    "planned_qty": 1000,
                    "completed_qty": 200,
                },
                {
                    "work_order": "WO001",
                    "product": "P001",
                    "planned_qty": 1000,
                    "completed_qty": 300,
                },
            ]
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0].planned_qty,
            1000,
        )
        self.assertEqual(
            result[0].completed_qty,
            500,
        )

    def test_planned_quantity_is_not_double_counted(
        self,
    ) -> None:
        result = self.service.build(
            [
                {
                    "work_order": "WO001",
                    "planned_qty": 1000,
                    "completed_qty": 100,
                },
                {
                    "work_order": "WO001",
                    "planned_qty": 1000,
                    "completed_qty": 200,
                },
            ]
        )

        self.assertEqual(
            result[0].planned_qty,
            1000,
        )

    def test_supports_alternative_field_names(
        self,
    ) -> None:
        item = self.service.build_one(
            {
                "work_order_no": "WO002",
                "product_code": "P002",
                "target_qty": 500,
                "ok_quantity": 250,
            }
        )

        self.assertEqual(
            item.work_order,
            "WO002",
        )
        self.assertEqual(
            item.product,
            "P002",
        )
        self.assertEqual(
            item.progress_percent,
            50.0,
        )

    def test_supports_object_rows(self) -> None:
        item = self.service.build_one(
            ProgressRow(
                work_order="WO003",
                product="P003",
                planned_qty=200,
                completed_qty=150,
            )
        )

        self.assertEqual(
            item.work_order,
            "WO003",
        )
        self.assertEqual(
            item.completed_qty,
            150,
        )

    def test_missing_work_order_is_skipped(
        self,
    ) -> None:
        result = self.service.build(
            [
                {
                    "planned_qty": 100,
                    "completed_qty": 50,
                }
            ]
        )

        self.assertEqual(result, [])

    def test_invalid_numbers_are_zero(self) -> None:
        item = self.service.build_one(
            {
                "work_order": "WO004",
                "planned_qty": "invalid",
                "completed_qty": None,
            }
        )

        self.assertEqual(
            item.planned_qty,
            0,
        )
        self.assertEqual(
            item.completed_qty,
            0,
        )
        self.assertEqual(
            item.progress_percent,
            0.0,
        )

    def test_negative_completed_qty_is_zero(
        self,
    ) -> None:
        item = self.service.build_one(
            {
                "work_order": "WO005",
                "planned_qty": 100,
                "completed_qty": -20,
            }
        )

        self.assertEqual(
            item.completed_qty,
            0,
        )
        self.assertEqual(
            item.remaining_qty,
            100,
        )

    def test_only_highest_operation_is_counted(self) -> None:
        result = self.service.build(
            [
                {
                    "work_order": "WO006",
                    "product": "P006",
                    "planned_qty": 100,
                    "completed_qty": 90,
                    "op_no": "OP1",
                    "execution_status": "COMPLETED",
                },
                {
                    "work_order": "WO006",
                    "product": "P006",
                    "planned_qty": 100,
                    "completed_qty": 80,
                    "op_no": "OP2",
                    "execution_status": "COMPLETED",
                },
            ]
        )[0]

        self.assertEqual(result.completed_qty, 80)

    def test_running_and_cancelled_output_is_ignored(self) -> None:
        item = self.service.build(
            [
                {
                    "work_order": "WO007",
                    "planned_qty": 100,
                    "completed_qty": 30,
                    "op_no": "OP2",
                    "execution_status": "STOPPED",
                },
                {
                    "work_order": "WO007",
                    "planned_qty": 100,
                    "completed_qty": 20,
                    "op_no": "OP2",
                    "execution_status": "RUNNING",
                },
                {
                    "work_order": "WO007",
                    "planned_qty": 100,
                    "completed_qty": 10,
                    "op_no": "OP2",
                    "execution_status": "CANCELLED",
                },
            ]
        )[0]

        self.assertEqual(item.completed_qty, 30)

    def test_running_final_op_does_not_fall_back_to_lower_op(
        self,
    ) -> None:
        item = self.service.build(
            [
                {
                    "work_order": "WO007B",
                    "planned_qty": 100,
                    "completed_qty": 60,
                    "op_no": "OP1",
                    "execution_status": "COMPLETED",
                },
                {
                    "work_order": "WO007B",
                    "planned_qty": 100,
                    "completed_qty": 20,
                    "op_no": "OP2",
                    "execution_status": "RUNNING",
                },
            ]
        )[0]

        self.assertEqual(item.completed_qty, 0)

    def test_latest_dated_plan_can_decrease(self) -> None:
        item = self.service.build(
            [
                {
                    "work_order": "WO008",
                    "planned_qty": 120,
                    "completed_qty": 20,
                    "plan_date": "2026-07-20",
                },
                {
                    "work_order": "WO008",
                    "planned_qty": 100,
                    "completed_qty": 30,
                    "plan_date": "2026-07-21",
                },
            ]
        )[0]

        self.assertEqual(item.planned_qty, 100)
        self.assertEqual(item.completed_qty, 50)

    def test_conflicting_product_for_work_order_rejected(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "exactly one Product",
        ):
            self.service.build(
                [
                    {
                        "work_order": "WO009",
                        "product": "P001",
                        "planned_qty": 100,
                    },
                    {
                        "work_order": "WO009",
                        "product": "P002",
                        "planned_qty": 100,
                    },
                ]
            )


if __name__ == "__main__":
    unittest.main()
