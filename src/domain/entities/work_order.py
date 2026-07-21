from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .base_entity import BaseEntity


@dataclass(slots=True)
class WorkOrder(BaseEntity):
    # Legacy fields
    work_order: str = ""
    quantity: int = 0
    plan_date: date | str | None = None

    # Current fields
    work_order_no: str = ""
    product_code: str = ""
    plan_qty: int = 0
    start_date: date | str | None = None
    due_date: date | str | None = None

    priority: str = "NORMAL"
    status: str = "PLANNED"
    remark: str = ""

    def __post_init__(self):
        if self.work_order and not self.work_order_no:
            self.work_order_no = self.work_order

        if self.quantity and not self.plan_qty:
            self.plan_qty = self.quantity

        if self.plan_date and not self.start_date:
            self.start_date = self.plan_date

        if self.start_date and not self.due_date:
            self.due_date = self.start_date