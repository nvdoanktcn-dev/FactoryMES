from __future__ import annotations

import os
import unittest

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication

from src.ui.controllers.pareto_controller import (
    ParetoController,
    ParetoMode,
)
from src.ui.widgets.pareto_widget import ParetoWidget


class TestParetoController(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = (
            QApplication.instance()
            or QApplication([])
        )

    def setUp(self) -> None:
        self.widget = ParetoWidget()
        self.controller = ParetoController(
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
                "machine": "BL01",
                "product": "P01",
                "work_order": "WO01",
                "operator": "NV01",
                "ng_type": "Gia công",
                "ng": 10,
            },
            {
                "machine": "BL02",
                "product": "P01",
                "work_order": "WO02",
                "operator": "NV02",
                "ng_type": "Phôi",
                "ng": 5,
            },
            {
                "machine": "BL01",
                "product": "P02",
                "work_order": "WO01",
                "operator": "NV01",
                "ng_type": "Gia công",
                "ng": 8,
            },
        ]

    def test_initial_mode(self) -> None:
        self.assertEqual(
            self.controller.mode,
            ParetoMode.BY_MACHINE,
        )

    def test_initial_title(self) -> None:
        self.assertEqual(
            self.widget.title(),
            "Pareto NG theo máy",
        )

    def test_invalid_widget(self) -> None:
        with self.assertRaises(TypeError):
            ParetoController(object())

    def test_set_data(self) -> None:
        result = self.controller.set_data(
            self.sample_rows()
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "BL01")
        self.assertEqual(result[0].value, 18.0)
        self.assertEqual(self.widget.point_count(), 2)

    def test_set_mode_product(self) -> None:
        self.controller.set_data(
            self.sample_rows()
        )

        result = self.controller.set_mode(
            ParetoMode.BY_PRODUCT
        )

        self.assertEqual(result[0].name, "P01")
        self.assertEqual(result[0].value, 15.0)
        self.assertEqual(
            self.widget.title(),
            "Pareto NG theo sản phẩm",
        )

    def test_set_mode_string_alias(self) -> None:
        self.controller.set_data(
            self.sample_rows()
        )

        result = self.controller.set_mode(
            "by_work_order"
        )

        self.assertEqual(result[0].name, "WO01")

    def test_invalid_mode(self) -> None:
        with self.assertRaises(ValueError):
            self.controller.set_mode(
                "invalid"
            )

    def test_set_value_field(self) -> None:
        rows = [
            {
                "machine": "BL01",
                "total_ng": 20,
            }
        ]

        self.controller.set_data(rows)
        result = self.controller.set_value_field(
            "total_ng"
        )

        self.assertEqual(result[0].value, 20.0)

    def test_empty_value_field(self) -> None:
        with self.assertRaises(ValueError):
            ParetoController(
                self.widget,
                value_field="",
            )

    def test_clear(self) -> None:
        self.controller.set_data(
            self.sample_rows()
        )

        self.controller.clear()

        self.assertEqual(
            self.controller.rows,
            (),
        )
        self.assertEqual(
            self.controller.source_rows,
            (),
        )
        self.assertEqual(
            self.widget.point_count(),
            0,
        )

    def test_set_none_clears(self) -> None:
        self.controller.set_data(
            self.sample_rows()
        )

        result = self.controller.set_data(None)

        self.assertEqual(result, ())
        self.assertEqual(
            self.widget.point_count(),
            0,
        )

    def test_refresh(self) -> None:
        self.controller.set_data(
            self.sample_rows()
        )

        self.widget.clear()

        result = self.controller.refresh()

        self.assertEqual(len(result), 2)
        self.assertEqual(
            self.widget.point_count(),
            2,
        )

    def test_custom_title(self) -> None:
        self.controller.set_title(
            "Top lỗi CNC"
        )

        self.assertEqual(
            self.widget.title(),
            "Top lỗi CNC",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)