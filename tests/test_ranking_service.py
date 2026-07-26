from __future__ import annotations

import math
import unittest
from dataclasses import dataclass

from src.services.ranking_service import (
    RankingItem,
    RankingService,
)


@dataclass
class FakeRow:
    name: str
    value: float


class TestRankingService(unittest.TestCase):

    def test_empty_rows(self) -> None:
        self.assertEqual(
            RankingService.build([]),
            (),
        )

    def test_build_from_dicts(self) -> None:
        result = RankingService.build([
            {"name": "A", "value": 20},
            {"name": "B", "value": 10},
        ])

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "A")
        self.assertEqual(result[0].rank, 1)
        self.assertAlmostEqual(result[0].percent, 66.6666667)

    def test_build_from_objects(self) -> None:
        result = RankingService.build([
            FakeRow("A", 5),
            FakeRow("B", 10),
        ])

        self.assertEqual(result[0].name, "B")
        self.assertEqual(result[0].value, 10.0)

    def test_descending_false(self) -> None:
        result = RankingService.build(
            [
                {"name": "A", "value": 20},
                {"name": "B", "value": 10},
            ],
            descending=False,
        )

        self.assertEqual(result[0].name, "B")

    def test_negative_values_become_zero(self) -> None:
        result = RankingService.build([
            {"name": "A", "value": -10},
        ])

        self.assertEqual(result[0].value, 0.0)

    def test_invalid_values_become_zero(self) -> None:
        result = RankingService.build([
            {"name": "A", "value": "invalid"},
        ])

        self.assertEqual(result[0].value, 0.0)

    def test_non_finite_values_become_zero(self) -> None:
        result = RankingService.build([
            {"name": "A", "value": math.nan},
            {"name": "B", "value": math.inf},
            {"name": "C", "value": -math.inf},
        ])

        self.assertTrue(
            all(item.value == 0.0 for item in result)
        )
        self.assertTrue(
            all(math.isfinite(item.percent) for item in result)
        )

    def test_equal_values_share_rank_and_keep_order(
        self,
    ) -> None:
        result = RankingService.build([
            {"name": "A", "value": 10},
            {"name": "B", "value": 10},
            {"name": "C", "value": 5},
        ])

        self.assertEqual(
            [item.name for item in result],
            ["A", "B", "C"],
        )
        self.assertEqual(
            [item.rank for item in result],
            [1, 1, 3],
        )

    def test_zero_total(self) -> None:
        result = RankingService.build([
            {"name": "A", "value": 0},
            {"name": "B", "value": 0},
        ])

        self.assertEqual(result[0].percent, 0.0)
        self.assertEqual(result[1].cumulative_percent, 0.0)

    def test_cumulative_percent_ends_at_100(self) -> None:
        result = RankingService.build([
            {"name": "A", "value": 30},
            {"name": "B", "value": 20},
            {"name": "C", "value": 10},
        ])

        self.assertAlmostEqual(
            result[-1].cumulative_percent,
            100.0,
        )

    def test_custom_fields(self) -> None:
        result = RankingService.build(
            [
                {"machine": "BL01", "ng": 7},
                {"machine": "BL02", "ng": 3},
            ],
            key="machine",
            value="ng",
        )

        self.assertEqual(result[0].name, "BL01")
        self.assertEqual(result[0].value, 7.0)

    def test_result_is_tuple(self) -> None:
        result = RankingService.build([
            {"name": "A", "value": 1},
        ])

        self.assertIsInstance(result, tuple)
        self.assertIsInstance(result[0], RankingItem)


if __name__ == "__main__":
    unittest.main(verbosity=2)
