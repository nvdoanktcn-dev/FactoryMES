from __future__ import annotations

import math
import os
import unittest
from dataclasses import dataclass
from datetime import date, datetime

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication

from src.ui.widgets.oee_trend_widget import (
    OEETrendWidget,
    TrendPoint,
)


@dataclass
class FakeTrendRow:
    report_date: date
    oee: float
    availability: float
    performance: float
    quality: float


class TestOEETrendWidget(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.app = (
            QApplication.instance()
            or QApplication([])
        )

    def setUp(self) -> None:
        self.widget = OEETrendWidget()

    def tearDown(self) -> None:
        self.widget.close()
        self.widget.deleteLater()
        self.app.processEvents()

    @staticmethod
    def sample_rows() -> list[dict]:
        return [
            {
                "label": "01/07",
                "oee": 72.5,
                "availability": 83.0,
                "performance": 90.0,
                "quality": 97.0,
            },
            {
                "label": "02/07",
                "oee": 81.0,
                "availability": 88.0,
                "performance": 94.0,
                "quality": 98.0,
            },
        ]

    def test_initial_state_is_empty(self) -> None:
        self.assertEqual(
            self.widget.point_count(),
            0,
        )
        self.assertEqual(
            self.widget.data(),
            (),
        )

    def test_default_title(self) -> None:
        self.assertEqual(
            self.widget.title(),
            "OEE Trend",
        )

    def test_set_title(self) -> None:
        self.widget.set_title(
            "Monthly OEE Trend"
        )

        self.assertEqual(
            self.widget.title(),
            "Monthly OEE Trend",
        )

    def test_set_mapping_data(self) -> None:
        self.widget.set_data(
            self.sample_rows()
        )

        self.assertEqual(
            self.widget.point_count(),
            2,
        )

        first = self.widget.data()[0]

        self.assertEqual(
            first.label,
            "01/07",
        )
        self.assertEqual(
            first.oee,
            72.5,
        )

    def test_set_trend_point_data(self) -> None:
        point = TrendPoint(
            label="03/07",
            oee=83.0,
            availability=91.0,
            performance=94.0,
            quality=98.0,
        )

        self.widget.set_data([point])

        self.assertEqual(
            self.widget.data(),
            (point,),
        )

    def test_set_object_data(self) -> None:
        row = FakeTrendRow(
            report_date=date(
                2026,
                7,
                4,
            ),
            oee=84.0,
            availability=90.0,
            performance=95.0,
            quality=99.0,
        )

        self.widget.set_data([row])

        point = self.widget.data()[0]

        self.assertEqual(
            point.label,
            "04/07",
        )
        self.assertEqual(
            point.oee,
            84.0,
        )

    def test_date_label_is_formatted(self) -> None:
        self.widget.set_data([
            {
                "report_date": date(
                    2026,
                    7,
                    5,
                ),
                "oee": 80,
            }
        ])

        self.assertEqual(
            self.widget.data()[0].label,
            "05/07",
        )

    def test_datetime_label_is_formatted(self) -> None:
        self.widget.set_data([
            {
                "date": datetime(
                    2026,
                    7,
                    6,
                    8,
                    30,
                ),
                "oee": 80,
            }
        ])

        self.assertEqual(
            self.widget.data()[0].label,
            "06/07",
        )

    def test_missing_values_become_zero(self) -> None:
        self.widget.set_data([
            {
                "label": "07/07",
            }
        ])

        point = self.widget.data()[0]

        self.assertEqual(
            point.oee,
            0.0,
        )
        self.assertEqual(
            point.availability,
            0.0,
        )
        self.assertEqual(
            point.performance,
            0.0,
        )
        self.assertEqual(
            point.quality,
            0.0,
        )

    def test_percentage_strings_are_converted(self) -> None:
        self.widget.set_data([
            {
                "label": "08/07",
                "oee": "82.5%",
                "availability": "90%",
                "performance": "93.25",
                "quality": "98.5%",
            }
        ])

        point = self.widget.data()[0]

        self.assertEqual(
            point.oee,
            82.5,
        )
        self.assertEqual(
            point.availability,
            90.0,
        )
        self.assertEqual(
            point.performance,
            93.25,
        )
        self.assertEqual(
            point.quality,
            98.5,
        )

    def test_invalid_values_become_zero(self) -> None:
        self.widget.set_data([
            {
                "label": "09/07",
                "oee": "invalid",
                "availability": None,
                "performance": object(),
                "quality": "",
            }
        ])

        point = self.widget.data()[0]

        self.assertEqual(
            point.oee,
            0.0,
        )
        self.assertEqual(
            point.availability,
            0.0,
        )
        self.assertEqual(
            point.performance,
            0.0,
        )
        self.assertEqual(
            point.quality,
            0.0,
        )

    def test_nan_and_infinity_become_zero(self) -> None:
        self.widget.set_data([
            {
                "label": "10/07",
                "oee": math.nan,
                "availability": math.inf,
                "performance": -math.inf,
                "quality": 98,
            }
        ])

        point = self.widget.data()[0]

        self.assertEqual(
            point.oee,
            0.0,
        )
        self.assertEqual(
            point.availability,
            0.0,
        )
        self.assertEqual(
            point.performance,
            0.0,
        )
        self.assertEqual(
            point.quality,
            98.0,
        )

    def test_values_are_clamped_to_percentage_range(self) -> None:
        self.widget.set_data([
            {
                "label": "11/07",
                "oee": 150,
                "availability": -10,
                "performance": 101,
                "quality": -1,
            }
        ])

        point = self.widget.data()[0]

        self.assertEqual(
            point.oee,
            100.0,
        )
        self.assertEqual(
            point.availability,
            0.0,
        )
        self.assertEqual(
            point.performance,
            100.0,
        )
        self.assertEqual(
            point.quality,
            0.0,
        )

    def test_none_data_clears_widget(self) -> None:
        self.widget.set_data(
            self.sample_rows()
        )

        self.widget.set_data(None)

        self.assertEqual(
            self.widget.point_count(),
            0,
        )

    def test_clear(self) -> None:
        self.widget.set_data(
            self.sample_rows()
        )

        self.widget.clear()

        self.assertEqual(
            self.widget.data(),
            (),
        )

    def test_all_series_are_visible_by_default(self) -> None:
        for series in (
            "oee",
            "availability",
            "performance",
            "quality",
        ):
            self.assertTrue(
                self.widget.is_series_visible(
                    series
                )
            )

    def test_series_can_be_hidden_and_shown(self) -> None:
        self.widget.set_series_visible(
            "quality",
            False,
        )

        self.assertFalse(
            self.widget.is_series_visible(
                "quality"
            )
        )

        self.widget.set_series_visible(
            "quality",
            True,
        )

        self.assertTrue(
            self.widget.is_series_visible(
                "quality"
            )
        )

    def test_series_name_is_case_insensitive(self) -> None:
        self.widget.set_series_visible(
            " OEE ",
            False,
        )

        self.assertFalse(
            self.widget.is_series_visible(
                "oee"
            )
        )

    def test_unknown_series_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            self.widget.set_series_visible(
                "downtime",
                False,
            )

        with self.assertRaises(KeyError):
            self.widget.is_series_visible(
                "downtime"
            )

    def test_data_returns_tuple(self) -> None:
        self.widget.set_data(
            self.sample_rows()
        )

        self.assertIsInstance(
            self.widget.data(),
            tuple,
        )

    def test_large_dataset_is_accepted(self) -> None:
        rows = [
            {
                "label": str(index),
                "oee": index % 101,
                "availability": 90,
                "performance": 95,
                "quality": 99,
            }
            for index in range(500)
        ]

        self.widget.set_data(rows)

        self.assertEqual(
            self.widget.point_count(),
            500,
        )

    def test_widget_renders_offscreen(self) -> None:
        self.widget.resize(
            800,
            420,
        )
        self.widget.set_data(
            self.sample_rows()
        )
        self.widget.show()
        self.app.processEvents()

        image = self.widget.grab()

        self.assertFalse(
            image.isNull()
        )
        self.assertGreater(
            image.width(),
            0,
        )
        self.assertGreater(
            image.height(),
            0,
        )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )