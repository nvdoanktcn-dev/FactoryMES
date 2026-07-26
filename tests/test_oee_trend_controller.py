from __future__ import annotations

import os
import unittest
from dataclasses import dataclass
from datetime import date
from types import SimpleNamespace

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication

from src.ui.controllers.oee_trend_controller import (
    OEETrendController,
)
from src.ui.widgets.oee_trend_widget import (
    OEETrendWidget,
    TrendPoint,
)


@dataclass
class FakeDashboard:
    trend: list[dict]


class TestOEETrendController(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.app = (
            QApplication.instance()
            or QApplication([])
        )

    def setUp(self) -> None:
        self.widget = OEETrendWidget()
        self.controller = OEETrendController(
            self.widget
        )

    def tearDown(self) -> None:
        self.widget.close()
        self.widget.deleteLater()
        self.app.processEvents()

    @staticmethod
    def sample_rows() -> list[dict]:
        return [
            {
                "report_date": date(
                    2026,
                    7,
                    1,
                ),
                "oee": 75.0,
                "availability": 85.0,
                "performance": 90.0,
                "quality": 98.0,
            }
        ]

    def test_controller_initial_state(self) -> None:
        self.assertIs(
            self.controller.widget,
            self.widget,
        )
        self.assertEqual(
            self.controller.rows,
            (),
        )

    def test_invalid_widget_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            OEETrendController(
                object()
            )

    def test_set_trend_data_updates_widget(self) -> None:
        result = self.controller.set_trend_data(
            self.sample_rows()
        )

        self.assertEqual(
            len(result),
            1,
        )
        self.assertEqual(
            self.widget.point_count(),
            1,
        )
        self.assertEqual(
            result[0].label,
            "01/07",
        )

    def test_set_trend_data_returns_tuple(self) -> None:
        result = self.controller.set_trend_data(
            self.sample_rows()
        )

        self.assertIsInstance(
            result,
            tuple,
        )
        self.assertIsInstance(
            result[0],
            TrendPoint,
        )

    def test_update_dashboard(self) -> None:
        dashboard = FakeDashboard(
            trend=self.sample_rows()
        )

        result = self.controller.update_dashboard(
            dashboard
        )

        self.assertEqual(
            len(result),
            1,
        )
        self.assertEqual(
            result[0].oee,
            75.0,
        )
        self.assertEqual(
            self.widget.point_count(),
            1,
        )

    def test_update_dashboard_supports_simple_namespace(self) -> None:
        dashboard = SimpleNamespace(
            trend=[
                {
                    "label": "02/07",
                    "oee": 84,
                }
            ]
        )

        result = self.controller.update_dashboard(
            dashboard
        )

        self.assertEqual(
            result[0].label,
            "02/07",
        )
        self.assertEqual(
            result[0].oee,
            84.0,
        )

    def test_update_none_clears_controller(self) -> None:
        self.controller.set_trend_data(
            self.sample_rows()
        )

        result = self.controller.update_dashboard(
            None
        )

        self.assertEqual(
            result,
            (),
        )
        self.assertEqual(
            self.controller.rows,
            (),
        )
        self.assertEqual(
            self.widget.point_count(),
            0,
        )

    def test_missing_trend_attribute_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            self.controller.update_dashboard(
                object()
            )

    def test_none_trend_data_clears_widget(self) -> None:
        self.controller.set_trend_data(
            self.sample_rows()
        )

        result = self.controller.set_trend_data(
            None
        )

        self.assertEqual(
            result,
            (),
        )
        self.assertEqual(
            self.widget.point_count(),
            0,
        )

    def test_clear(self) -> None:
        self.controller.set_trend_data(
            self.sample_rows()
        )

        self.controller.clear()

        self.assertEqual(
            self.controller.rows,
            (),
        )
        self.assertEqual(
            self.widget.point_count(),
            0,
        )

    def test_refresh_restores_controller_rows(self) -> None:
        rows = [
            {
                "label": "01/07",
                "oee": 80,
            },
            {
                "label": "02/07",
                "oee": 82,
            },
        ]

        self.controller.set_trend_data(rows)

        self.widget.clear()

        self.assertEqual(
            self.widget.point_count(),
            0,
        )

        result = self.controller.refresh()

        self.assertEqual(
            self.widget.point_count(),
            2,
        )
        self.assertEqual(
            len(result),
            2,
        )

    def test_rows_property_is_read_only_tuple(self) -> None:
        self.controller.set_trend_data(
            self.sample_rows()
        )

        rows = self.controller.rows

        self.assertIsInstance(
            rows,
            tuple,
        )
        self.assertEqual(
            len(rows),
            1,
        )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )