from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .base_entity import BaseEntity


@dataclass(slots=True)
class ProductionOrder(BaseEntity):
    work_order_no: str
    product_code: str
    operation_no: int
    operation_name: str
    process_type: str

    machine_type: str = ""
    machine_code: str = ""
    employee_code: str = ""
    shift: str = ""

    plan_qty: int = 0
    completed_qty: int = 0
    ng_qty: int = 0

    status: str = "PLANNED"

    planned_start: datetime | None = None
    planned_finish: datetime | None = None
    actual_start: datetime | None = None
    actual_finish: datetime | None = None

    remark: str = ""