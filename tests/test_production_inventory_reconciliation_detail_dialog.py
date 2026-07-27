from __future__ import annotations

from src.ui.dialogs.production_inventory_reconciliation_detail_dialog import (
    ProductionInventoryReconciliationDetailDialog,
)
from tests.qt_test_utils import get_test_app


class FakeService:
    def export_detail(self, detail, output_path):
        del detail
        return output_path


def _detail():
    return {
        "selected_row": {
            "work_order_no": "WO-1",
            "product_code": "P-1",
            "plan_qty": 120,
            "completed_qty": 90,
            "ng_qty": 3,
            "inventory_qty": 80,
            "reconciliation_status":
                "PENDING_INVENTORY",
        },
        "daily_detail": [{
            "date": "2026-07-01",
            "final_op_qty": 90,
            "ng_qty": 3,
            "inventory_qty": 0,
            "daily_variance": 90,
            "cumulative_production": 90,
            "cumulative_inventory": 0,
            "cumulative_pending": 90,
            "cumulative_over": 0,
        }],
        "production_detail": [{
            "production_log_id": 2,
            "operation": "OP20",
            "is_final_operation": True,
            "ok_qty": 90,
            "ng_qty": 2,
        }],
        "inventory_receipts": [{
            "inventory_id": 8,
            "inventory_date": "2026-07-02",
            "qty": 80,
            "import_log_id": 4,
            "import_file": "inventory.xlsx",
            "import_status": "SUCCESS",
        }],
    }


def test_detail_dialog_loads_all_tabs():
    get_test_app()
    dialog = (
        ProductionInventoryReconciliationDetailDialog(
            detail=_detail(),
            service=FakeService(),
        )
    )

    assert dialog.tabs.count() == 3
    assert dialog.daily_table.rowCount() == 1
    assert dialog.production_table.item(0, 3).text() == "OP20"
    assert dialog.production_table.item(0, 4).text() == "YES"
    assert dialog.inventory_table.item(0, 4).text() == "inventory.xlsx"

    dialog.close()
