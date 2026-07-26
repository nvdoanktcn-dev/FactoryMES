from __future__ import annotations

import os
import sys
import unittest

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.services.progress_service import (
    ProgressItem,
    ProgressStatus,
)
from src.ui.widgets.production_progress_widget import (
    ProductionProgressWidget,
    ProgressSortMode,
)


class TestProductionProgressWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = (
            QApplication.instance()
            or QApplication(sys.argv)
        )

    def setUp(self) -> None:
        self.widget = ProductionProgressWidget()

        self.items = [
            self._make_item(
                work_order="WO003",
                completed=200,
                planned=1000,
                status=ProgressStatus.IN_PROGRESS,
            ),
            self._make_item(
                work_order="WO001",
                completed=850,
                planned=1000,
                status=ProgressStatus.ON_TRACK,
            ),
            self._make_item(
                work_order="WO002",
                completed=1000,
                planned=1000,
                status=ProgressStatus.COMPLETED,
            ),
        ]

    def tearDown(self) -> None:
        self.widget.close()
        self.widget.deleteLater()
        self.app.processEvents()

    @staticmethod
    def _make_item(
        *,
        work_order: str,
        completed: int,
        planned: int,
        status: ProgressStatus,
    ) -> ProgressItem:
        remaining = max(planned - completed, 0)
        over_completed = max(completed - planned, 0)

        progress = (
            completed / planned * 100
            if planned > 0
            else 0
        )

        return ProgressItem(
            work_order=work_order,
            product=f"PRODUCT-{work_order}",
            planned_qty=planned,
            completed_qty=completed,
            remaining_qty=remaining,
            over_completed_qty=over_completed,
            progress_percent=round(progress, 2),
            display_percent=min(
                round(progress, 2),
                100.0,
            ),
            status=status,
        )

    def test_widget_created(self) -> None:
        self.assertIsNotNone(self.widget.table)
        self.assertIsNotNone(
            self.widget.sort_combo
        )

    def test_default_sort_mode(self) -> None:
        self.assertEqual(
            self.widget.sort_mode,
            ProgressSortMode.WORK_ORDER,
        )

    def test_empty_on_creation(self) -> None:
        self.assertEqual(
            self.widget.data,
            (),
        )
        self.assertEqual(
            self.widget.table.rowCount(),
            0,
        )

    def test_set_data(self) -> None:
        self.widget.set_data(self.items)

        self.assertEqual(
            self.widget.data,
            tuple(self.items),
        )
        self.assertEqual(
            self.widget.table.rowCount(),
            3,
        )

    def test_default_sort_by_work_order(self) -> None:
        self.widget.set_data(self.items)

        self.assertEqual(
            [
                item.work_order
                for item in self.widget.display_data
            ],
            ["WO001", "WO002", "WO003"],
        )

    def test_sort_by_progress(self) -> None:
        self.widget.set_data(self.items)
        self.widget.sort_by_progress()

        self.assertEqual(
            [
                item.work_order
                for item in self.widget.display_data
            ],
            ["WO002", "WO001", "WO003"],
        )

    def test_sort_by_remaining(self) -> None:
        self.widget.set_data(self.items)
        self.widget.sort_by_remaining()

        self.assertEqual(
            [
                item.work_order
                for item in self.widget.display_data
            ],
            ["WO003", "WO001", "WO002"],
        )

    def test_clear(self) -> None:
        self.widget.set_data(self.items)
        self.widget.clear()

        self.assertEqual(
            self.widget.data,
            (),
        )
        self.assertEqual(
            self.widget.display_data,
            (),
        )
        self.assertEqual(
            self.widget.table.rowCount(),
            0,
        )

    def test_repeated_set_data(self) -> None:
        self.widget.set_data(self.items)
        self.widget.set_data(
            [self.items[0]]
        )

        self.assertEqual(
            self.widget.table.rowCount(),
            1,
        )

    def test_progress_bar_value(self) -> None:
        self.widget.set_data(
            [self.items[1]]
        )

        progress_bar = (
            self.widget.progress_bar_at(0)
        )

        self.assertIsNotNone(progress_bar)
        self.assertEqual(
            progress_bar.value(),
            85,
        )

    def test_over_completed_is_capped_at_100(
        self,
    ) -> None:
        item = self._make_item(
            work_order="WO004",
            completed=1200,
            planned=1000,
            status=ProgressStatus.OVER_COMPLETED,
        )

        self.widget.set_data([item])

        progress_bar = (
            self.widget.progress_bar_at(0)
        )

        self.assertEqual(
            progress_bar.value(),
            100,
        )
        self.assertEqual(
            progress_bar.format(),
            "120.00%",
        )

    def test_status_stored_in_progress_bar(
        self,
    ) -> None:
        self.widget.set_data(
            [self.items[1]]
        )

        progress_bar = (
            self.widget.progress_bar_at(0)
        )

        self.assertEqual(
            progress_bar.property(
                "progress_status"
            ),
            ProgressStatus.ON_TRACK.value,
        )

    def test_remaining_quantity_user_data(
        self,
    ) -> None:
        self.widget.set_data(
            [self.items[1]]
        )

        table_item = self.widget.table.item(
            0,
            self.widget.COLUMN_REMAINING,
        )

        self.assertEqual(
            table_item.data(
                Qt.ItemDataRole.UserRole
            ),
            150,
        )

    def test_invalid_sort_mode_raises_error(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            self.widget.set_sort_mode(
                "invalid"
            )


if __name__ == "__main__":
    unittest.main()