from datetime import date

from src.services.dashboard import (
    DashboardFacadeService,
    DashboardRequest,
)

service = DashboardFacadeService()

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

response = service.build(
    request
)

print(type(response).__name__)

print(type(response.analytics).__name__)

print(type(response.charts).__name__)

print(type(response.status).__name__)

print(len(response.records))

print(len(response.import_history))

print(len(response.alarms))