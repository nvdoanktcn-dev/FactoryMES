from datetime import date

from src.services.dashboard import (
    DashboardFacadeService,
    DashboardRequest,
)

service = DashboardFacadeService()

request = DashboardRequest(
    start_date=date(2026, 7, 1),
    end_date=date(2026, 7, 31),
)

r1 = service.build(request)
r2 = service.build(request)

print(r1 is r2)

print(
    service.cache_statistics()
)

service.invalidate_cache()

print(
    service.cache_statistics()
)