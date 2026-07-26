from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication

from src.services.trend_service import (
    TrendGranularity,
    TrendPoint,
)
from src.ui.widgets.trend_widget import TrendWidget


class TestTrendWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = (
            QApplication.instance()
            or QApplication(sys.argv)
        )

    def setUp(self) -> None:
        self.widget = TrendWidget()

        self.points = [
            TrendPoint(
                period_start=datetime(
                    2026, 7, 20
                ),
                label="20/07/2026",
                oee=80,
                availability=90,
                performance=85,
                quality=98,
                runtime_minutes=500,
                downtime_minutes=100,
                ok_qty=950,
                ng_qty=50,
                execution_count=5,
            ),
            TrendPoint(
                period_start=datetime(
                    2026, 7, 21
                ),
                label="21/07/2026",
                oee=85,
                availability=92,
                performance=90,
                quality=99,
                runtime_minutes=550,
                downtime_minutes=50,
                ok_qty=990,
                ng_qty=10,
                execution_count=6,
            ),
        ]

    def tearDown(self) -> None:
        self.widget.close()
        self.widget.deleteLater()
        self.app.processEvents()

    def test_widget_created(self) -> None:
        self.assertIsNotNone(self.widget.chart)
        self.assertIsNotNone(
            self.widget.chart_view
        )

    def test_default_granularity_is_daily(self) -> None:
        self.assertEqual(
            self.widget.granularity,
            TrendGranularity.DAILY,
        )

    def test_four_series_created(self) -> None:
        self.assertEqual(
            len(self.widget.series),
            4,
        )

        self.assertIn(
            "oee",
            self.widget.series,
        )
        self.assertIn(
            "availability",
            self.widget.series,
        )
        self.assertIn(
            "performance",
            self.widget.series,
        )
        self.assertIn(
            "quality",
            self.widget.series,
        )

    def test_empty_state_on_creation(self) -> None:
        self.assertEqual(
            self.widget.data,
            (),
        )
        self.assertTrue(
            self.widget.empty_label.isVisible()
            or self.widget.empty_label.isHidden() is False
        )

    def test_set_data_stores_points(self) -> None:
        self.widget.set_data(self.points)

        self.assertEqual(
            self.widget.data,
            tuple(self.points),
        )

    def test_set_data_populates_series(self) -> None:
        self.widget.set_data(self.points)

        for series in self.widget.series.values():
            self.assertEqual(
                series.count(),
                2,
            )

    def test_oee_series_contains_expected_value(
        self,
    ) -> None:
        self.widget.set_data(self.points)

        oee_series = self.widget.series["oee"]

        self.assertAlmostEqual(
            oee_series.at(0).y(),
            80.0,
        )
        self.assertAlmostEqual(
            oee_series.at(1).y(),
            85.0,
        )

    def test_fractional_percentage_is_converted(
        self,
    ) -> None:
        point = TrendPoint(
            period_start=datetime(2026, 7, 20),
            label="20/07/2026",
            oee=0.8,
            availability=0.9,
            performance=0.85,
            quality=0.98,
            runtime_minutes=100,
            downtime_minutes=10,
            ok_qty=95,
            ng_qty=5,
            execution_count=1,
        )

        self.widget.set_data([point])

        self.assertAlmostEqual(
            self.widget.series["oee"].at(0).y(),
            80.0,
        )

    def test_clear_removes_all_data(self) -> None:
        self.widget.set_data(self.points)
        self.widget.clear()

        self.assertEqual(
            self.widget.data,
            (),
        )

        for series in self.widget.series.values():
            self.assertEqual(
                series.count(),
                0,
            )

    def test_set_data_can_be_called_repeatedly(
        self,
    ) -> None:
        self.widget.set_data(self.points)
        self.widget.set_data(
            [self.points[1]]
        )

        self.assertEqual(
            len(self.widget.data),
            1,
        )

        for series in self.widget.series.values():
            self.assertEqual(
                series.count(),
                1,
            )

    def test_set_granularity(self) -> None:
        self.widget.set_granularity(
            TrendGranularity.MONTHLY
        )

        self.assertEqual(
            self.widget.granularity,
            TrendGranularity.MONTHLY,
        )

    def test_yearly_granularity(self) -> None:
        self.widget.set_granularity(
            TrendGranularity.YEARLY
        )

        self.assertEqual(
            self.widget.granularity,
            TrendGranularity.YEARLY,
        )

    def test_invalid_granularity_raises_error(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            self.widget.set_granularity(
                "quarterly"
            )

    def test_non_finite_percentage_is_zero(self) -> None:
        point = TrendPoint(
            period_start=datetime(2026, 7, 20),
            label="20/07/2026",
            oee=float("nan"),
            availability=float("inf"),
            performance=80,
            quality=90,
            runtime_minutes=100,
            downtime_minutes=10,
            ok_qty=95,
            ng_qty=5,
            execution_count=1,
        )

        self.widget.set_data([point])

        self.assertEqual(
            self.widget.series["oee"].at(0).y(),
            0.0,
        )
        self.assertEqual(
            self.widget.series["availability"].at(0).y(),
            0.0,
        )

    def test_granularity_signal(self) -> None:
        received = []

        self.widget.granularity_changed.connect(
            received.append
        )

        self.widget.set_granularity(
            TrendGranularity.WEEKLY
        )

        self.assertEqual(
            received[-1],
            TrendGranularity.WEEKLY,
        )


if __name__ == "__main__":
    unittest.main()
