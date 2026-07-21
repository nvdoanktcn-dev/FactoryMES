from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class DashboardResponse:

    analytics: Any

    charts: Any

    status: Any

    records: Any

    import_history: Any

    alarms: Any