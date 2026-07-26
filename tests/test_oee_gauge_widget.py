from __future__ import annotations

import unittest

from PySide6.QtTest import QSignalSpy
from PySide6.QtGui import QColor

from src.ui.widgets.oee_gauge_widget import (
    OEEGaugeWidget,
)
from tests.helpers.qt_test_helper import (
    get_test_app,
)


class TestOEEGaugeWidget(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.app = get_test_app()

    def setUp(self) -> None:
        self.widget = OEEGaugeWidget()

    def tearDown(self) -> None:
        widget = getattr(
            self,
            "widget",
            None,
        )

        if widget is not None:
            widget.close()
            widget.deleteLater()

    def test_widget_created(self) -> None:
        self.assertIsNotNone(
            self.widget
        )
        self.assertEqual(
            self.widget.value(),
            0.0,
        )
        self.assertEqual(
            self.widget.title(),
            "OEE",
        )
        self.assertEqual(
            self.widget.suffix(),
            "%",
        )

    def test_set_numeric_value(self) -> None:
        self.widget.set_value(82.5)

        self.assertEqual(
            self.widget.value(),
            82.5,
        )

    def test_set_numeric_string(self) -> None:
        self.widget.set_value(
            "91.25"
        )

        self.assertEqual(
            self.widget.value(),
            91.25,
        )

    def test_set_percentage_string(self) -> None:
        self.widget.set_value(
            "87.50%"
        )

        self.assertEqual(
            self.widget.value(),
            87.5,
        )

    def test_set_comma_numeric_string(self) -> None:
        self.widget.set_value(
            "1,000"
        )

        self.assertEqual(
            self.widget.value(),
            100.0,
        )

    def test_value_above_100_is_clamped(self) -> None:
        self.widget.set_value(120)

        self.assertEqual(
            self.widget.value(),
            100.0,
        )

    def test_negative_value_is_clamped(self) -> None:
        self.widget.set_value(-5)

        self.assertEqual(
            self.widget.value(),
            0.0,
        )

    def test_none_becomes_zero(self) -> None:
        self.widget.set_value(75)
        self.widget.set_value(None)

        self.assertEqual(
            self.widget.value(),
            0.0,
        )

    def test_invalid_text_becomes_zero(self) -> None:
        self.widget.set_value(75)
        self.widget.set_value(
            "invalid"
        )

        self.assertEqual(
            self.widget.value(),
            0.0,
        )

    def test_nan_becomes_zero(self) -> None:
        self.widget.set_value(
            float("nan")
        )

        self.assertEqual(
            self.widget.value(),
            0.0,
        )

    def test_infinity_becomes_zero(self) -> None:
        self.widget.set_value(
            float("inf")
        )

        self.assertEqual(
            self.widget.value(),
            0.0,
        )

    def test_clear(self) -> None:
        self.widget.set_value(88)
        self.widget.clear()

        self.assertEqual(
            self.widget.value(),
            0.0,
        )

    def test_value_changed_signal(self) -> None:
        spy = QSignalSpy(
            self.widget.value_changed
        )

        self.widget.set_value(72.5)

        self.assertEqual(
            spy.count(),
            1,
        )
        self.assertEqual(
            spy.at(0)[0],
            72.5,
        )

    def test_same_value_does_not_emit_signal(self) -> None:
        self.widget.set_value(72.5)

        spy = QSignalSpy(
            self.widget.value_changed
        )

        self.widget.set_value(72.5)

        self.assertEqual(
            spy.count(),
            0,
        )

    def test_set_title(self) -> None:
        self.widget.set_title(
            "Overall OEE"
        )

        self.assertEqual(
            self.widget.title(),
            "Overall OEE",
        )

    def test_none_title_becomes_empty(self) -> None:
        self.widget.set_title(None)

        self.assertEqual(
            self.widget.title(),
            "",
        )

    def test_set_suffix(self) -> None:
        self.widget.set_suffix(
            " percent"
        )

        self.assertEqual(
            self.widget.suffix(),
            " percent",
        )

    def test_green_threshold_color(self) -> None:
        color = (
            OEEGaugeWidget
            .color_for_value(85)
        )

        self.assertEqual(
            color,
            QColor(46, 125, 50),
        )

    def test_yellow_threshold_color(self) -> None:
        color = (
            OEEGaugeWidget
            .color_for_value(60)
        )

        self.assertEqual(
            color,
            QColor(245, 166, 35),
        )

    def test_red_color(self) -> None:
        color = (
            OEEGaugeWidget
            .color_for_value(59.99)
        )

        self.assertEqual(
            color,
            QColor(198, 40, 40),
        )

    def test_good_status(self) -> None:
        self.assertEqual(
            OEEGaugeWidget
            .status_for_value(90),
            "Good",
        )

    def test_warning_status(self) -> None:
        self.assertEqual(
            OEEGaugeWidget
            .status_for_value(70),
            "Warning",
        )

    def test_critical_status(self) -> None:
        self.assertEqual(
            OEEGaugeWidget
            .status_for_value(40),
            "Critical",
        )

    def test_qt_property_get_and_set(self) -> None:
        self.widget.setProperty(
            "qt_value",
            66.5,
        )

        self.assertEqual(
            self.widget.property(
                "qt_value"
            ),
            66.5,
        )

    def test_widget_can_render_offscreen(self) -> None:
        self.widget.resize(
            320,
            240,
        )
        self.widget.set_value(
            78.25
        )

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
