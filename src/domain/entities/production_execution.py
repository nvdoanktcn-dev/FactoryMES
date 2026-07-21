from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .base_entity import BaseEntity


@dataclass(slots=True)
class ProductionExecution(BaseEntity):
    assignment_id: int
    start_time: datetime

    end_time: datetime | None = None

    ok_qty: int = 0
    ng_qty: int = 0
    processing_ng_qty: int = 0
    blank_ng_qty: int = 0

    runtime_minutes: float = 0.0
    downtime_minutes: float = 0.0

    status: str = "RUNNING"
    remark: str = ""