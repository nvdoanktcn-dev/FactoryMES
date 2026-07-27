from __future__ import annotations

import src.ui.pages.production_inventory_reconciliation_page as page_module
from src.ui.pages.production_inventory_reconciliation_page import (
    ProductionInventoryReconciliationPage,
)
from tests.qt_test_utils import get_test_app


class FakeReportService:
    def __init__(self):
        self.detail_calls = []

    def build_report(self, *args, **kwargs):
        del args, kwargs
        return {
            "summary": {
                "pending_inventory_qty": 10,
                "over_received_qty": 0,
            },
            "rows": [{
                "work_order_no": "WO-1",
                "product_code": "P-1",
                "plan_qty": 120,
                "completed_qty": 90,
                "ng_qty": 3,
                "inventory_qty": 80,
                "pending_inventory_qty": 10,
                "over_received_qty": 0,
                "remaining_plan_qty": 30,
                "completion_percent": 75,
                "inventory_percent": 88.89,
                "reconciliation_status":
                    "PENDING_INVENTORY",
            }],
        }

    def build_detail(
        self,
        *args,
        **kwargs,
    ):
        self.detail_calls.append((args, kwargs))
        return {
            "selected_row": {
                "work_order_no": "WO-1",
                "product_code": "P-1",
            },
            "daily_detail": [],
            "production_detail": [],
            "inventory_receipts": [],
        }


class FakeDetailDialog:
    created = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.exec_count = 0
        self.__class__.created.append(self)

    def exec(self):
        self.exec_count += 1
        return 0


def test_page_opens_detail_for_selected_order(
    monkeypatch,
):
    get_test_app()
    service = FakeReportService()
    monkeypatch.setattr(
        page_module,
        "ProductionInventoryReconciliationDetailDialog",
        FakeDetailDialog,
    )
    FakeDetailDialog.created.clear()
    page = ProductionInventoryReconciliationPage(
        service=service
    )

    page.load_report()
    assert page.detail_button.isEnabled()

    page.show_selected_detail()

    assert len(service.detail_calls) == 1
    assert service.detail_calls[0][1][
        "work_order_no"
    ] == "WO-1"
    assert service.detail_calls[0][1][
        "product_code"
    ] == "P-1"
    assert FakeDetailDialog.created[0].exec_count == 1

    page.close()
