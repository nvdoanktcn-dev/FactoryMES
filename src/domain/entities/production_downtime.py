from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .base_entity import BaseEntity


@dataclass(slots=True)
class ProductionDowntime(BaseEntity):
    execution_id: int
    reason_code: str
    reason_name: str
    start_time: datetime

    end_time: datetime | None = None
    duration_minutes: float = 0.0

    status: str = "OPEN"
    remark: str = ""