from src.ui.pages.reporting_page import (
    ReportingPage,
)
from tests.qt_test_utils import get_test_app


class FakeReportService:
    def __init__(self):
        self.closed = False

    def build_report(self, *args, **kwargs):
        del args, kwargs
        return {
            "record_count": 1,
            "machine": [{
                "machine_code": "BL01",
                "record_count": 1,
                "runtime_hour": 1,
                "downtime_hour": 0,
                "net_runtime_hour": 1,
                "ok_qty": 10,
                "ng_qty": 0,
                "total_qty": 10,
                "utilization_percent": 100,
                "oee_percent": 100,
            }],
        }

    def export_report(self, report, output_path):
        del report
        return output_path

    def close(self):
        self.closed = True


def test_reporting_page_loads_machine_rows():
    get_test_app()
    service = FakeReportService()
    page = ReportingPage(service=service)

    page.load_report()

    assert page.table.rowCount() == 1
    assert page.table.item(0, 0).text() == "BL01"
    assert page.export_button.isEnabled()


def test_injected_report_service_is_not_closed():
    get_test_app()
    service = FakeReportService()
    page = ReportingPage(service=service)

    page.close_resources()

    assert service.closed is False
