from dataclasses import dataclass


@dataclass(slots=True)
class WorkOrderProgressResult:
    work_order_no: str
    plan_qty: int
    completed_qty: int
    ng_qty: int
    remaining_qty: int
    progress_percent: float
    current_status: str
    suggested_status: str
    is_complete: bool