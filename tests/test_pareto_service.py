from __future__ import annotations

import unittest
from dataclasses import dataclass

from src.services.pareto_service import ParetoService


@dataclass
class FakeNGRow:
    machine: str
    product: str
    ng: float


class TestParetoService(unittest.TestCase):

    def test_empty_rows(self) -> None:
        result = ParetoService.build(
            [],
            group_field="machine",
            value_field="ng",
        )

        self.assertEqual(result, ())

    def test_group_dict_rows(self) -> None:
        result = ParetoService.build(
            [
                {"machine": "BL01", "ng": 10},
                {"machine": "BL01", "ng": 8},
                {"machine": "BL02", "ng": 5},
            ],
            group_field="machine",
            value_field="ng",
        )

        self.assertEqual(result[0].name, "BL01")
        self.assertEqual(result[0].value, 18.0)
        self.assertEqual(result[1].value, 5.0)

    def test_group_object_rows(self) -> None:
        result = ParetoService.build(
            [
                FakeNGRow("BL01", "P01", 4),
                FakeNGRow("BL01", "P02", 6),
            ],
            group_field="machine",
            value_field="ng",
        )

        self.assertEqual(result[0].value, 10.0)

    def test_group_by_product(self) -> None:
        result = ParetoService.build(
            [
                {"product": "P01", "ng": 10},
                {"product": "P02", "ng": 5},
                {"product": "P01", "ng": 2},
            ],
            group_field="product",
            value_field="ng",
        )

        self.assertEqual(result[0].name, "P01")
        self.assertEqual(result[0].value, 12.0)

    def test_negative_values_are_zero(self) -> None:
        result = ParetoService.build(
            [{"machine": "BL01", "ng": -10}],
            group_field="machine",
            value_field="ng",
        )

        self.assertEqual(result[0].value, 0.0)

    def test_invalid_values_are_skipped(self) -> None:
        result = ParetoService.build(
            [
                {"machine": "BL01", "ng": "bad"},
                {"machine": "BL02", "ng": 5},
            ],
            group_field="machine",
            value_field="ng",
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "BL02")
        self.assertEqual(result[0].value, 5.0)

    def test_missing_group_field(self) -> None:
        result = ParetoService.build(
            [{"ng": 4}],
            group_field="machine",
            value_field="ng",
        )

        self.assertEqual(result[0].name, "")
        self.assertEqual(result[0].value, 4.0)

    def test_percentage_total(self) -> None:
        result = ParetoService.build(
            [
                {"machine": "BL01", "ng": 8},
                {"machine": "BL02", "ng": 2},
            ],
            group_field="machine",
            value_field="ng",
        )

        self.assertAlmostEqual(
            result[-1].cumulative_percent,
            100.0,
        )

    def test_only_final_operation_ng_is_counted(self) -> None:
        result = ParetoService.build(
            [
                {
                    "machine": "BL01",
                    "work_order": "WO-001",
                    "product": "P-001",
                    "op_no": "OP1",
                    "ng": 10,
                },
                {
                    "machine": "BL02",
                    "work_order": "WO-001",
                    "product": "P-001",
                    "op_no": "OP2",
                    "ng": 3,
                },
            ],
            group_field="machine",
            value_field="ng",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "BL02")
        self.assertEqual(result[0].value, 3)

    def test_running_cancelled_and_inactive_are_excluded(
        self,
    ) -> None:
        result = ParetoService.build(
            [
                {
                    "machine": "BL01",
                    "work_order": "WO-001",
                    "op_no": "OP2",
                    "ng": 4,
                    "status": "COMPLETED",
                },
                {
                    "machine": "BL01",
                    "work_order": "WO-001",
                    "op_no": "OP2",
                    "ng": 9,
                    "status": "RUNNING",
                },
                {
                    "machine": "BL01",
                    "work_order": "WO-001",
                    "op_no": "OP2",
                    "ng": 8,
                    "status": "CANCELLED",
                },
                {
                    "machine": "BL01",
                    "work_order": "WO-001",
                    "op_no": "OP3",
                    "ng": 7,
                    "routing_status": "INACTIVE",
                },
            ],
            group_field="machine",
            value_field="ng",
        )

        self.assertEqual(result[0].value, 4)

    def test_non_finite_value_is_zero(self) -> None:
        result = ParetoService.build(
            [
                {"machine": "BL01", "ng": float("nan")},
                {"machine": "BL02", "ng": float("inf")},
            ],
            group_field="machine",
            value_field="ng",
        )

        self.assertTrue(
            all(item.value == 0 for item in result)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
