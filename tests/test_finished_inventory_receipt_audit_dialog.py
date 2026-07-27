import json
from datetime import datetime
from types import SimpleNamespace

from src.ui.dialogs.finished_inventory_receipt_audit_dialog import (
    FinishedInventoryReceiptAuditDialog,
)
from tests.qt_test_utils import get_test_app


class FakeService:
    def __init__(self):
        self.closed = False

    def get_receipt_audit_history(self, limit=500):
        del limit
        return [
            SimpleNamespace(
                id=2,
                created_at=datetime(2026, 7, 27, 15, 0),
                record_id=7,
                action="UPDATE",
                old_value=json.dumps({
                    "source": "MANUAL",
                    "data": {
                        "work_order": "WO-1",
                        "product_code": "P-1",
                        "inventory_date": "2026-07-27",
                        "qty": 20,
                    },
                }),
                new_value=json.dumps({
                    "source": "MANUAL",
                    "data": {
                        "work_order": "WO-1",
                        "product_code": "P-1",
                        "inventory_date": "2026-07-27",
                        "qty": 30,
                    },
                }),
                username="System",
            ),
            SimpleNamespace(
                id=1,
                created_at=datetime(2026, 7, 27, 14, 0),
                record_id=6,
                action="CREATE",
                old_value=None,
                new_value=json.dumps({
                    "source": "EXCEL_IMPORT",
                    "data": {
                        "work_order": "WO-2",
                        "product_code": "P-2",
                        "inventory_date": "2026-07-27",
                        "qty": 50,
                    },
                }),
                username="System",
            ),
        ]

    def close(self):
        self.closed = True


def test_dialog_loads_and_filters_audit_records():
    get_test_app()
    service = FakeService()
    dialog = FinishedInventoryReceiptAuditDialog(
        service=service
    )

    assert dialog.table.rowCount() == 2
    assert dialog.table.item(0, 3).text() == "UPDATE"
    assert "Qty: 20" in dialog.table.item(0, 6).text()
    assert "Qty: 30" in dialog.table.item(0, 7).text()

    dialog.source_filter.setCurrentText(
        "EXCEL_IMPORT"
    )

    assert dialog.table.rowCount() == 1
    assert dialog.table.item(0, 3).text() == "CREATE"
    assert dialog.table.item(0, 4).text() == (
        "EXCEL_IMPORT"
    )

    dialog.close()
    assert service.closed is False


def test_rollback_is_disabled_for_rollback_action():
    get_test_app()
    service = FakeService()
    record = service.get_receipt_audit_history()[0]
    record.action = "ROLLBACK"
    service.get_receipt_audit_history = (
        lambda limit=500: [record]
    )
    dialog = FinishedInventoryReceiptAuditDialog(
        service=service
    )

    assert not dialog.rollback_button.isEnabled()
    dialog.close()
