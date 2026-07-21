from datetime import date
from types import SimpleNamespace

from src.services.dashboard import (
    DashboardRequest,
    DashboardResponse,
)
from src.ui.dashboard.dashboard_controller import (
    DashboardController,
)


class FakePanel:
    def __init__(self):
        self.data = None

    def update_data(self, data):
        self.data = data

    def update_status(self, data):
        self.data = data


class FakePage:
    def __init__(self):
        self.kpi_panel = FakePanel()
        self.chart_panel = FakePanel()
        self.table_panel = FakePanel()
        self.status_panel = FakePanel()


class FakeFacade:
    def __init__(self):
        self.request = None

    def build(self, request):
        self.request = request

        return DashboardResponse(
            analytics={
                "summary": {
                    "total_qty": 100
                }
            },
            charts={
                "daily_output": []
            },
            status={
                "dashboard": {
                    "status": "ONLINE"
                }
            },
            records=[],
            import_history=[],
            alarms=[],
        )

    def invalidate_cache(self):
        pass

    def cache_statistics(self):
        return {
            "count": 0
        }

    def build_without_cache(
        self,
        request,
    ):
        return self.build(
            request
        )


def test_dashboard_controller_refresh():
    page = FakePage()
    facade = FakeFacade()

    controller = DashboardController(
        page=page,
        facade_service=facade,
    )

    request = DashboardRequest(
        start_date=date(
            2026,
            7,
            1,
        ),
        end_date=date(
            2026,
            7,
            31,
        ),
    )

    response = controller.refresh(
        request
    )

    assert response.analytics[
        "summary"
    ][
        "total_qty"
    ] == 100

    assert (
        facade.request
        is request
    )

    assert page.kpi_panel.data[
        "summary"
    ][
        "total_qty"
    ] == 100

    assert page.chart_panel.data == {
        "daily_output": []
    }

    assert page.status_panel.data[
        "dashboard"
    ][
        "status"
    ] == "ONLINE"