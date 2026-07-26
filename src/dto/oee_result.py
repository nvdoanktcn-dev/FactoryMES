from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class OEEResult:
    availability: float
    performance: float
    quality: float
    oee: float

    runtime_minutes: float
    downtime_minutes: float

    total_qty: int
    ok_qty: int
    ng_qty: int
