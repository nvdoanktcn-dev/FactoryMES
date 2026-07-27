from src.ui.pages.production_inventory_reconciliation_page import (
    ProductionInventoryReconciliationPage,
)
from tests.qt_test_utils import get_test_app


class FakeReportService:
    def __init__(self):
        self.closed = False

    def build_report(self, *args, **kwargs):
        del args, kwargs
        return {
            "record_count": 1,
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

    def export_report(self, report, output_path):
        del report
        return output_path

    def close(self):
        self.closed = True


def test_page_loads_reconciliation_rows():
    get_test_app()
    service = FakeReportService()
    page = ProductionInventoryReconciliationPage(
        service=service
    )

    page.load_report()

    assert page.table.rowCount() == 1
    assert page.table.item(0, 0).text() == "WO-1"
    assert page.table.columnCount() == 12
    assert page.table.horizontalHeaderItem(4).text() == "NG"
    assert page.table.item(0, 4).text() == "3"
    assert page.table.item(0, 5).text() == "80"
    assert page.table.item(0, 6).text() == "10"
    assert page.export_button.isEnabled()


def test_injected_service_is_not_closed():
    get_test_app()
    service = FakeReportService()
    page = ProductionInventoryReconciliationPage(
        service=service
    )

    page.close_resources()

    assert service.closed is False
