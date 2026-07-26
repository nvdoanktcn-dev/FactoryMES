from __future__ import annotations

import os
import unittest
from unittest.mock import Mock

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication

from src.ui.controllers.pareto_controller import (
    ParetoController,
    ParetoMode,
)
from src.ui.models.oee_dashboard_models import (
    OEEDashboardData,
)
from src.ui.pages.oee_dashboard_page import (
    OEEDashboardPage,
)
from src.ui.widgets.pareto_widget import (
    ParetoWidget,
)


class FakeDashboardController:

    def __init__(self) -> None:
        self.calls = 0

    def load_dashboard(self, filters):
        del filters

        self.calls += 1

        return OEEDashboardData(
            summary={
                "execution_count": 3,
                "oee": 80,
            },
            by_machine=[
                {
                    "group_label": "BL01",
                    "ng_quantity": 18,
                },
                {
                    "group_label": "BL02",
                    "ng_quantity": 5,
                },
            ],
            by_employee=[
                {
                    "group_label": "NV01",
                    "ng_quantity": 12,
                },
                {
                    "group_label": "NV02",
                    "ng_quantity": 4,
                },
            ],
            by_work_order=[
                {
                    "group_label": "WO01",
                    "ng_quantity": 15,
                },
                {
                    "group_label": "WO02",
                    "ng_quantity": 8,
                },
            ],
            by_product=[
                {
                    "group_label": "P01",
                    "ng_quantity": 20,
                },
                {
                    "group_label": "P02",
                    "ng_quantity": 3,
                },
            ],
            by_operation=[],
        )


class TestOEEDashboardParetoIntegration(
    unittest.TestCase
):

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = (
            QApplication.instance()
            or QApplication([])
        )

    def setUp(self) -> None:
        self.dashboard_controller = (
            FakeDashboardController()
        )

        self.page = OEEDashboardPage(
            controller=self.dashboard_controller,
            export_service=Mock(),
        )

        self.app.processEvents()

    def tearDown(self) -> None:
        self.page.close()
        self.page.deleteLater()
        self.app.processEvents()

    def test_pareto_widget_created(self) -> None:
        self.assertIsInstance(
            self.page.pareto_widget,
            ParetoWidget,
        )

    def test_pareto_controller_created(self) -> None:
        self.assertIsInstance(
            self.page.pareto_controller,
            ParetoController,
        )

    def test_pareto_tab_exists(self) -> None:
        tab_titles = [
            self.page.tabs.tabText(index)
            for index in range(
                self.page.tabs.count()
            )
        ]

        self.assertIn(
            "Pareto NG",
            tab_titles,
        )

    def test_initial_mode_is_machine(self) -> None:
        self.assertEqual(
            self.page.pareto_controller.mode,
            ParetoMode.BY_MACHINE,
        )

    def test_initial_machine_data(self) -> None:
        rows = self.page.pareto_controller.rows

        self.assertEqual(
            len(rows),
            2,
        )
        self.assertEqual(
            rows[0].name,
            "BL01",
        )
        self.assertEqual(
            rows[0].value,
            18.0,
        )

    def test_change_mode_to_product(self) -> None:
        product_index = (
            self.page.pareto_mode_combo
            .findData(
                ParetoMode.BY_PRODUCT
            )
        )

        self.page.pareto_mode_combo.setCurrentIndex(
            product_index
        )

        self.app.processEvents()

        rows = self.page.pareto_controller.rows

        self.assertEqual(
            rows[0].name,
            "P01",
        )
        self.assertEqual(
            rows[0].value,
            20.0,
        )

    def test_change_mode_to_work_order(
        self,
    ) -> None:
        index = (
            self.page.pareto_mode_combo
            .findData(
                ParetoMode.BY_WORK_ORDER
            )
        )

        self.page.pareto_mode_combo.setCurrentIndex(
            index
        )

        self.app.processEvents()

        self.assertEqual(
            self.page.pareto_controller.rows[0].name,
            "WO01",
        )

    def test_change_mode_to_operator(
        self,
    ) -> None:
        index = (
            self.page.pareto_mode_combo
            .findData(
                ParetoMode.BY_OPERATOR
            )
        )

        self.page.pareto_mode_combo.setCurrentIndex(
            index
        )

        self.app.processEvents()

        self.assertEqual(
            self.page.pareto_controller.rows[0].name,
            "NV01",
        )

    def test_refresh_updates_pareto(self) -> None:
        initial_calls = (
            self.dashboard_controller.calls
        )

        self.page.refresh()
        self.app.processEvents()

        self.assertGreater(
            self.dashboard_controller.calls,
            initial_calls,
        )

        self.assertEqual(
            self.page.pareto_widget.point_count(),
            2,
        )

    def test_clear_dashboard_clears_pareto(
        self,
    ) -> None:
        self.assertGreater(
            self.page.pareto_widget.point_count(),
            0,
        )

        self.page._clear_dashboard()

        self.assertEqual(
            self.page.pareto_widget.point_count(),
            0,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)