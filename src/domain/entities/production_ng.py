from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .base_entity import BaseEntity


@dataclass(slots=True)
class ProductionNG(BaseEntity):
    execution_id: int
    ng_type: str
    reason_code: str
    reason_name: str
    quantity: int

    recorded_at: datetime | None = None
    employee_code: str = ""
    remark: str = ""
    status: str = "ACTIVE"