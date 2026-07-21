from __future__ import annotations

import unittest
from dataclasses import dataclass

from src.ui.controllers.top_machine_controller import TopMachineController
from src.ui.widgets.top_machine_widget import MachineRow, TopMachineWidget
from tests.helpers.qt_test_helper import get_test_app


@dataclass
class FakeMachineBreakdown:
    group_key: str
    group_label: str = ""
    availability: float = 0.0
    performance: float = 0.0
    quality: float = 0.0
    oee: float = 0.0
    runtime_minutes: float = 0.0
    downtime_minutes: float = 0.0
    ok_quantity: int = 0
    ng_quantity: int = 0


class TestTopMachineController(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.app = get_test_app()

    def setUp(self) -> None:
        self.widget = TopMachineWidget()
        self.controller = TopMachineController(self.widget)

    def tearDown(self) -> None:
        widget = getattr(self, "widget", None)
        if widget is not None:
            widget.close()
            widget.deleteLater()

    def test_controller_created(self) -> None:
        self.assertIs(self.controller.widget, self.widget)
        self.assertEqual(self.controller.rows, ())

    def test_invalid_widget_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            TopMachineController(object())

    def test_set_machine_data_with_machine_rows(self) -> None:
        source = [
            MachineRow(machine="BL01", oee=91.5, availability=95.0, performance=97.0, quality=99.0,
                       runtime=520.0, downtime=15.0, ok_qty=2000, ng_qty=10),
            MachineRow(machine="BL02", oee=82.0, availability=88.0, performance=94.0, quality=99.0,
                       runtime=480.0, downtime=30.0, ok_qty=1800, ng_qty=20),
        ]

        result = self.controller.set_machine_data(source)

        self.assertEqual(len(result), 2)
        self.assertEqual(len(self.controller.rows), 2)
        self.assertEqual(self.widget.table.rowCount(), 2)
        self.assertEqual(self.widget.table.item(0, 1).text(), "BL01")

    def test_set_machine_data_with_dashboard_mapping(self) -> None:
        source = [{
            "group_key": "BR01",
            "group_label": "Robot BR01",
            "availability": 90.0,
            "performance": 92.0,
            "quality": 98.0,
            "oee": 81.14,
            "runtime_minutes": 600.0,
            "downtime_minutes": 45.0,
            "ok_quantity": 2500,
            "ng_quantity": 30,
        }]

        result = self.controller.set_machine_data(source)
        row = result[0]

        self.assertEqual(len(result), 1)
        self.assertEqual(row.machine, "Robot BR01")
        self.assertAlmostEqual(row.oee, 81.14)
        self.assertAlmostEqual(row.runtime, 600.0)
        self.assertAlmostEqual(row.downtime, 45.0)
        self.assertEqual(row.ok_qty, 2500)
        self.assertEqual(row.ng_qty, 30)
        self.assertEqual(self.widget.table.rowCount(), 1)
        self.assertEqual(self.widget.table.item(0, 1).text(), "Robot BR01")

    def test_mapping_falls_back_to_group_key(self) -> None:
        result = self.controller.set_machine_data([{"group_key": "ASK01", "oee": 75.0}])
        self.assertEqual(result[0].machine, "ASK01")

    def test_mapping_supports_widget_field_names(self) -> None:
        source = [{
            "machine": "BL05",
            "oee": 86.0,
            "runtime": 400.0,
            "downtime": 25.0,
            "ok_qty": 1500,
            "ng_qty": 12,
        }]

        row = self.controller.set_machine_data(source)[0]

        self.assertEqual(row.machine, "BL05")
        self.assertEqual(row.runtime, 400.0)
        self.assertEqual(row.downtime, 25.0)
        self.assertEqual(row.ok_qty, 1500)
        self.assertEqual(row.ng_qty, 12)

    def test_set_machine_data_with_object(self) -> None:
        source = [FakeMachineBreakdown(
            group_key="BL07",
            group_label="CNC BL07",
            availability=96.0,
            performance=93.0,
            quality=99.0,
            oee=88.39,
            runtime_minutes=720.0,
            downtime_minutes=18.0,
            ok_quantity=3100,
            ng_quantity=15,
        )]

        row = self.controller.set_machine_data(source)[0]

        self.assertEqual(row.machine, "CNC BL07")
        self.assertAlmostEqual(row.oee, 88.39)
        self.assertAlmostEqual(row.runtime, 720.0)
        self.assertAlmostEqual(row.downtime, 18.0)
        self.assertEqual(row.ok_qty, 3100)
        self.assertEqual(row.ng_qty, 15)

    def test_numeric_strings_are_converted(self) -> None:
        source = [{
            "machine": "BL09",
            "oee": "87.50%",
            "availability": "90",
            "performance": "95.5",
            "quality": "99.2",
            "runtime": "1,200.5",
            "downtime": "35",
            "ok_qty": "3,500",
            "ng_qty": "18",
        }]

        row = self.controller.set_machine_data(source)[0]

        self.assertAlmostEqual(row.oee, 87.5)
        self.assertAlmostEqual(row.availability, 90.0)
        self.assertAlmostEqual(row.performance, 95.5)
        self.assertAlmostEqual(row.quality, 99.2)
        self.assertAlmostEqual(row.runtime, 1200.5)
        self.assertEqual(row.ok_qty, 3500)
        self.assertEqual(row.ng_qty, 18)

    def test_invalid_numeric_values_become_zero(self) -> None:
        row = self.controller.set_machine_data([{
            "machine": "BL10",
            "oee": "invalid",
            "runtime": None,
            "ok_qty": "not-a-number",
        }])[0]

        self.assertEqual(row.oee, 0.0)
        self.assertEqual(row.runtime, 0.0)
        self.assertEqual(row.ok_qty, 0)

    def test_refresh_restores_controller_rows_to_widget(self) -> None:
        self.controller.set_machine_data([
            MachineRow(machine="BL01", oee=90.0),
            MachineRow(machine="BL02", oee=80.0),
        ])
        self.widget.set_data([])
        self.assertEqual(self.widget.table.rowCount(), 0)

        self.controller.refresh()

        self.assertEqual(self.widget.table.rowCount(), 2)

    def test_clear_removes_controller_and_widget_data(self) -> None:
        self.controller.set_machine_data([MachineRow(machine="BL01", oee=90.0)])
        self.controller.clear()

        self.assertEqual(self.controller.rows, ())
        self.assertEqual(self.widget.table.rowCount(), 0)

    def test_none_machine_data_clears_controller(self) -> None:
        self.controller.set_machine_data([MachineRow(machine="BL01", oee=90.0)])
        result = self.controller.set_machine_data(None)

        self.assertEqual(result, [])
        self.assertEqual(self.controller.rows, ())
        self.assertEqual(self.widget.table.rowCount(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
