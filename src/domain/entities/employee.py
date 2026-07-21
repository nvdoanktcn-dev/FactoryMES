from __future__ import annotations

from dataclasses import dataclass

from .base_entity import BaseEntity


@dataclass(slots=True)
class Employee(BaseEntity):
    employee_code: str
    employee_name: str
    department: str = ""
    position: str = ""
    shift: str = ""
    status: str = "ACTIVE"
    remark: str = ""