from __future__ import annotations

from dataclasses import dataclass

from .base_entity import BaseEntity


@dataclass(slots=True)
class Machine(BaseEntity):
    machine_code: str
    machine_name: str
    machine_type: str = ""
    line: str = ""
    location: str = ""
    brand: str = ""
    model: str = ""
    serial_number: str = ""
    status: str = "RUNNING"
