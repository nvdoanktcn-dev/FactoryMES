from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .base_entity import BaseEntity


@dataclass(slots=True)
class ProductionAssignment(BaseEntity):
    production_order_id: int

    machine_code: str = ""
    employee_code: str = ""
    shift: str = ""

    planned_start: datetime | None = None
    planned_finish: datetime | None = None

    status: str = "DRAFT"

    assigned_at: datetime | None = None
    released_at: datetime | None = None
    actual_start: datetime | None = None
    actual_finish: datetime | None = None

    remark: str = ""