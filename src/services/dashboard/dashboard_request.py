from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(slots=True)
class DashboardRequest:
    start_date: date
    end_date: date

    shift: Optional[str] = None

    machine_code: Optional[str] = None

    employee_code: Optional[str] = None

    product_code: Optional[str] = None

    work_order_no: Optional[str] = None

    auto_refresh: bool = False

    refresh_interval: int = 60