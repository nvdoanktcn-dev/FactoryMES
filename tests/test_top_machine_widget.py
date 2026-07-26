from __future__ import annotations

import unittest
from math import inf, nan

from src.ui.widgets.top_machine_widget import MachineRow, TopMachineWidget
from tests.helpers.qt_test_helper import get_test_app


class TestTopMachineWidget(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.app = get_test_app()

    def setUp(self) -> None:
        self.widget = TopMachineWidget()

    def tearDown(self) -> None:
        widget = getattr(self, "widget", None)
        if widget is not None:
            widget.close()
            widget.deleteLater()

    def sample_rows(self) -> list[MachineRow]:
        return [
            MachineRow(
                machine="MC01",
                oee=92,
                availability=96,
                performance=93,
                quality=98,
                runtime=520,
                downtime=15,
                ok_qty=2000,
                ng_qty=12,
            ),
            MachineRow(
                machine="MC02",
                oee=81,
                availability=85,
                performance=86,
                quality=96,
                runtime=610,
                downtime=42,
                ok_qty=2500,
                ng_qty=24,
            ),
            MachineRow(
                machine="MC03",
                oee=67,
                availability=71,
                performance=78,
                quality=90,
                runtime=410,
                downtime=80,
                ok_qty=1800,
                ng_qty=60,
            ),
            MachineRow(
                machine="MC04",
                oee=55,
                availability=60,
                performance=65,
                quality=82,
                runtime=350,
                downtime=120,
                ok_qty=1400,
                ng_qty=130,
            ),
            MachineRow(
                machine="MC05",
                oee=88,
                availability=91,
                performance=90,
                quality=97,
                runtime=700,
                downtime=20,
                ok_qty=3200,
                ng_qty=8,
            ),
        ]

    def test_widget_created(self) -> None:
        self.assertIsNotNone(self.widget)
        self.assertEqual(self.widget.table.rowCount(), 0)

    def test_set_data(self) -> None:
        rows = self.sample_rows()

        self.widget.set_data(rows)

        self.assertEqual(self.widget.table.rowCount(), len(rows))

    def test_top_limit(self) -> None:
        rows = self.sample_rows()
        rows.extend(
            [
                MachineRow(
                    machine=f"MC{i:02d}",
                    oee=float(i),
                    runtime=float(i * 10),
                    ok_qty=i * 100,
                )
                for i in range(6, 21)
            ]
        )

        self.widget.set_data(rows)
        self.widget.spin_top.setValue(5)
        self.widget.refresh()

        self.assertEqual(self.widget.table.rowCount(), 5)

    def test_sort_oee(self) -> None:
        self.widget.set_data(self.sample_rows())
        self.widget.cbo_sort.setCurrentText("OEE")
        self.widget.refresh()

        machine = self.widget.table.item(0, 1).text()

        self.assertEqual(machine, "MC01")

    def test_sort_runtime(self) -> None:
        self.widget.set_data(self.sample_rows())
        self.widget.cbo_sort.setCurrentText("Runtime")
        self.widget.refresh()

        machine = self.widget.table.item(0, 1).text()

        self.assertEqual(machine, "MC05")

    def test_sort_ng_quantity(self) -> None:
        self.widget.set_data(self.sample_rows())
        self.widget.cbo_sort.setCurrentText("NG Quantity")
        self.widget.refresh()

        machine = self.widget.table.item(0, 1).text()

        self.assertEqual(machine, "MC04")

    def test_empty_data(self) -> None:
        self.widget.set_data([])

        self.assertEqual(self.widget.table.rowCount(), 0)

    def test_none_clears_existing_data(self) -> None:
        self.widget.set_data(self.sample_rows())

        self.widget.set_data(None)

        self.assertEqual(self.widget.table.rowCount(), 0)

    def test_non_finite_values_are_rendered_as_zero(self) -> None:
        self.widget.set_data([
            MachineRow(
                machine="MC01",
                oee=nan,
                runtime=inf,
                ng_qty=inf,
            )
        ])

        self.assertEqual(self.widget.table.item(0, 2).text(), "0.00")
        self.assertEqual(self.widget.table.item(0, 3).text(), "0.00")
        self.assertEqual(self.widget.table.item(0, 6).text(), "0")

    def test_equal_values_share_competition_rank(self) -> None:
        self.widget.set_data([
            MachineRow(machine="MC01", oee=90),
            MachineRow(machine="MC02", oee=90),
            MachineRow(machine="MC03", oee=80),
        ])

        ranks = [
            self.widget.table.item(index, 0).text()
            for index in range(3)
        ]

        self.assertEqual(ranks, ["1", "1", "3"])

    def test_oee_color_green(self) -> None:
        color = self.widget._oee_color(90)

        self.assertEqual(color.getRgb()[:3], (198, 239, 206))

    def test_oee_color_yellow(self) -> None:
        color = self.widget._oee_color(70)

        self.assertEqual(color.getRgb()[:3], (255, 235, 156))

    def test_oee_color_red(self) -> None:
        color = self.widget._oee_color(40)

        self.assertEqual(color.getRgb()[:3], (255, 199, 206))


if __name__ == "__main__":
    unittest.main(verbosity=2)
