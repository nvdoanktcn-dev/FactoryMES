from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from src.ui.dialogs.finished_inventory_import_history_dialog import (
    FinishedInventoryImportHistoryDialog,
)
from tests.qt_test_utils import get_test_app


class FakeHistoryService:
    def __init__(self):
        self.rollback_ids = []

    def get_recent(self, limit=100):
        del limit
        return [
            SimpleNamespace(
                id=7,
                import_time=datetime(
                    2026, 7, 27, 14, 30
                ),
                file_name="inventory.xlsx",
                total_rows=3,
                inserted_rows=2,
                updated_rows=1,
                failed_rows=0,
                duration=0.25,
                status="SUCCESS",
                message=(
                    "Created: 2; Skipped: 1; Failed: 0."
                ),
            )
        ]

    def rollback_import(self, log_id):
        self.rollback_ids.append(log_id)
        return {
            "message": "Rollback completed."
        }


def test_history_dialog_loads_import_counts():
    get_test_app()
    dialog = FinishedInventoryImportHistoryDialog(
        service=FakeHistoryService()
    )

    assert dialog.table.rowCount() == 1
    assert dialog.table.item(0, 0).text() == "7"
    assert dialog.table.item(0, 4).text() == "2"
    assert dialog.table.item(0, 5).text() == "1"
    assert dialog.rollback_button.isEnabled()

    dialog.close()


def test_rolled_back_history_disables_rollback():
    get_test_app()
    service = FakeHistoryService()
    record = service.get_recent()[0]
    record.status = "ROLLED_BACK"
    service.get_recent = lambda limit=100: [record]

    dialog = FinishedInventoryImportHistoryDialog(
        service=service
    )

    assert dialog.rollback_button.isEnabled() is False
    dialog.close()
