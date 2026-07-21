from dataclasses import dataclass

from .base_entity import BaseEntity


@dataclass(slots=True)
class Routing(BaseEntity):
    # Legacy fields
    routing_code: str = ""

    # Current fields
    product_code: str = ""
    operation_no: int = 0
    operation_name: str = ""
    process_type: str = ""

    # Legacy alias
    machine_code: str = ""

    # Current field
    machine_type: str = ""

    # Legacy alias
    cycle_time: float = 0.0

    # Current fields
    standard_cycle_time_sec: float = 0.0
    standard_output_pcs_hour: float = 0.0
    standard_operator_count: float = 1.0

    status: str = "ACTIVE"
    remark: str = ""

    def __post_init__(self):
        if self.cycle_time and not self.standard_cycle_time_sec:
            self.standard_cycle_time_sec = self.cycle_time