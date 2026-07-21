from __future__ import annotations

from dataclasses import dataclass

from .base_entity import BaseEntity


@dataclass(slots=True)
class Product(BaseEntity):

    product_code: str

    product_name: str

    customer: str = ""

    drawing_no: str = ""

    revision: str = ""

    material: str = ""

    unit: str = "PCS"

    cycle_time: float = 0

    standard_output: float = 0

    product_group: str = ""

    status: str = "ACTIVE"

    remark: str = ""