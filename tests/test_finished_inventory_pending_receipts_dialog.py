from src.ui.dialogs.finished_inventory_pending_receipts_dialog import (
    FinishedInventoryPendingReceiptsDialog,
)
from tests.qt_test_utils import get_test_app


class FakeService:
    def __init__(self):
        self.closed = False

    def get_pending_receipts(self):
        return [{
            "work_order": "WO-100",
            "product_code": "P-100",
            "final_operation": 30,
            "final_op_qty": 120,
            "received_qty": 80,
            "available_qty": 40,
        }]

    def close(self):
        self.closed = True


def test_dialog_loads_pending_receipts():
    get_test_app()
    service = FakeService()
    dialog = (
        FinishedInventoryPendingReceiptsDialog(
            service=service
        )
    )

    assert dialog.table.rowCount() == 1
    assert dialog.table.item(0, 0).text() == "WO-100"
    assert dialog.table.item(0, 2).text() == "30"
    assert dialog.table.item(0, 5).text() == "40"
    assert dialog.receive_button.isEnabled()
    assert "Available Qty: 40" in (
        dialog.summary_label.text()
    )

    dialog.close()
    assert service.closed is False


def test_dialog_handles_empty_queue():
    get_test_app()
    service = FakeService()
    service.get_pending_receipts = lambda: []
    dialog = (
        FinishedInventoryPendingReceiptsDialog(
            service=service
        )
    )

    assert dialog.table.rowCount() == 0
    assert not dialog.receive_button.isEnabled()
    assert "Pending Work Orders: 0" in (
        dialog.summary_label.text()
    )

    dialog.close()
