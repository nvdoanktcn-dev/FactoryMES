from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ui.pages.oee_dashboard_page import OEEDashboardPage
from src.ui.widgets.top_machine_widget import TopMachineWidget


def get_app() -> QApplication:
    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv)

    return app


def create_dashboard_data(
    machine_rows: list[dict[str, Any]] | None = None,
) -> SimpleNamespace:
    """
    Tạo dữ liệu Dashboard giả có cùng cấu trúc mà
    OEEDashboardPage đang sử dụng.
    """

    return SimpleNamespace(
        summary={
            "execution_count": len(machine_rows or []),
            "planned_minutes": 960.0,
            "runtime_minutes": 850.0,
            "downtime_minutes": 110.0,
            "ok_quantity": 5000,
            "ng_quantity": 50,
            "total_quantity": 5050,
            "availability": 88.54,
            "performance": 92.0,
            "quality": 99.01,
            "oee": 80.67,
        },
        trend=[],
        by_machine=list(machine_rows or []),
        by_employee=[],
        by_work_order=[],
        by_product=[],
        by_operation=[],
    )


def create_pareto_data() -> SimpleNamespace:
    """
    Tạo dữ liệu Pareto rỗng nhưng hợp lệ.
    """

    empty_result = SimpleNamespace(items=[])

    return SimpleNamespace(
        downtime=empty_result,
        ng=empty_result,
    )


class FakeDashboardController:
    def __init__(
        self,
        dashboard_data: SimpleNamespace,
    ) -> None:
        self.dashboard_data = dashboard_data
        self.last_filters: Any = None
        self.load_count = 0

    def load_dashboard(
        self,
        filters: Any,
    ) -> SimpleNamespace:
        self.last_filters = filters
        self.load_count += 1

        return self.dashboard_data


class FakeParetoController:
    def __init__(self) -> None:
        self.last_filters: Any = None
        self.load_count = 0

    def load_all(
        self,
        filters: Any,
    ) -> SimpleNamespace:
        self.last_filters = filters
        self.load_count += 1

        return create_pareto_data()


class FakeExportService:
    def export(self, *args: Any, **kwargs: Any) -> Path:
        raise AssertionError(
            "Export không được gọi trong integration test này."
        )


class TestOEEDashboardTopMachineIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = get_app()

    def setUp(self) -> None:
        self.initial_machine_rows = [
            {
                "group_key": "BL01",
                "group_label": "CNC BL01",
                "execution_count": 10,
                "planned_minutes": 480.0,
                "runtime_minutes": 450.0,
                "downtime_minutes": 30.0,
                "ok_quantity": 2000,
                "ng_quantity": 10,
                "total_quantity": 2010,
                "availability": 93.75,
                "performance": 96.0,
                "quality": 99.50,
                "oee": 89.55,
            },
            {
                "group_key": "BR01",
                "group_label": "ROBOT BR01",
                "execution_count": 8,
                "planned_minutes": 480.0,
                "runtime_minutes": 400.0,
                "downtime_minutes": 80.0,
                "ok_quantity": 1800,
                "ng_quantity": 40,
                "total_quantity": 1840,
                "availability": 83.33,
                "performance": 90.0,
                "quality": 97.83,
                "oee": 73.37,
            },
        ]

        self.dashboard_controller = FakeDashboardController(
            create_dashboard_data(self.initial_machine_rows)
        )

        self.pareto_controller = FakeParetoController()

        self.page = OEEDashboardPage(
            controller=self.dashboard_controller,
            export_service=FakeExportService(),
            pareto_controller=self.pareto_controller,
        )

    def tearDown(self) -> None:
        self.page.close()
        self.page.deleteLater()
        self.app.processEvents()

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def test_top_machine_widget_created(self) -> None:
        self.assertTrue(
            hasattr(self.page, "top_machine_widget")
        )

        self.assertIsInstance(
            self.page.top_machine_widget,
            TopMachineWidget,
        )

    def test_top_machine_controller_created(self) -> None:
        self.assertTrue(
            hasattr(self.page, "top_machine_controller")
        )

        self.assertIs(
            self.page.top_machine_controller.widget,
            self.page.top_machine_widget,
        )

    # ------------------------------------------------------------------
    # Tab integration
    # ------------------------------------------------------------------

    def test_top_machine_tab_exists(self) -> None:
        tab_titles = [
            self.page.tabs.tabText(index)
            for index in range(self.page.tabs.count())
        ]

        self.assertIn(
            "Top Machine",
            tab_titles,
        )

    def test_top_machine_tab_uses_expected_widget(self) -> None:
        top_machine_index = -1

        for index in range(self.page.tabs.count()):
            if self.page.tabs.tabText(index) == "Top Machine":
                top_machine_index = index
                break

        self.assertGreaterEqual(
            top_machine_index,
            0,
        )

        self.assertIs(
            self.page.tabs.widget(top_machine_index),
            self.page.top_machine_widget,
        )

    # ------------------------------------------------------------------
    # Initial rendering
    # ------------------------------------------------------------------

    def test_initial_machine_data_is_rendered(self) -> None:
        table = self.page.top_machine_widget.table

        self.assertEqual(
            table.rowCount(),
            2,
        )

        first_machine = table.item(0, 1).text()
        second_machine = table.item(1, 1).text()

        self.assertEqual(
            first_machine,
            "CNC BL01",
        )

        self.assertEqual(
            second_machine,
            "ROBOT BR01",
        )

    def test_top_machine_data_matches_machine_breakdown(self) -> None:
        controller_rows = self.page.top_machine_controller.rows

        self.assertEqual(
            len(controller_rows),
            len(self.initial_machine_rows),
        )

        first_row = controller_rows[0]

        self.assertEqual(
            first_row.machine,
            "CNC BL01",
        )

        self.assertAlmostEqual(
            first_row.oee,
            89.55,
        )

        self.assertAlmostEqual(
            first_row.runtime,
            450.0,
        )

        self.assertAlmostEqual(
            first_row.downtime,
            30.0,
        )

        self.assertEqual(
            first_row.ok_qty,
            2000,
        )

        self.assertEqual(
            first_row.ng_qty,
            10,
        )

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def test_refresh_updates_top_machine_data(self) -> None:
        updated_rows = [
            {
                "group_key": "ASK01",
                "group_label": "ROBOT ASK01",
                "execution_count": 5,
                "planned_minutes": 480.0,
                "runtime_minutes": 470.0,
                "downtime_minutes": 10.0,
                "ok_quantity": 3000,
                "ng_quantity": 5,
                "total_quantity": 3005,
                "availability": 97.92,
                "performance": 98.0,
                "quality": 99.83,
                "oee": 95.78,
            }
        ]

        self.dashboard_controller.dashboard_data = (
            create_dashboard_data(updated_rows)
        )

        self.page.load_data()

        table = self.page.top_machine_widget.table

        self.assertEqual(
            table.rowCount(),
            1,
        )

        self.assertEqual(
            table.item(0, 1).text(),
            "ROBOT ASK01",
        )

        self.assertEqual(
            len(self.page.top_machine_controller.rows),
            1,
        )

        self.assertEqual(
            self.page.top_machine_controller.rows[0].machine,
            "ROBOT ASK01",
        )

    def test_refresh_calls_dashboard_and_pareto_controllers(self) -> None:
        initial_dashboard_calls = (
            self.dashboard_controller.load_count
        )

        initial_pareto_calls = (
            self.pareto_controller.load_count
        )

        self.page.load_data()

        self.assertEqual(
            self.dashboard_controller.load_count,
            initial_dashboard_calls + 1,
        )

        self.assertEqual(
            self.pareto_controller.load_count,
            initial_pareto_calls + 1,
        )

    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------

    def test_clear_dashboard_clears_top_machine_widget(self) -> None:
        self.assertGreater(
            self.page.top_machine_widget.table.rowCount(),
            0,
        )

        self.page._clear_dashboard()

        self.assertEqual(
            self.page.top_machine_widget.table.rowCount(),
            0,
        )

        self.assertEqual(
            self.page.top_machine_controller.rows,
            (),
        )

    # ------------------------------------------------------------------
    # Existing machine table remains available
    # ------------------------------------------------------------------

    def test_existing_machine_table_is_not_removed_yet(self) -> None:
        self.assertTrue(
            hasattr(self.page, "machine_table")
        )

        self.assertEqual(
            self.page.machine_table.rowCount(),
            len(self.initial_machine_rows),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)