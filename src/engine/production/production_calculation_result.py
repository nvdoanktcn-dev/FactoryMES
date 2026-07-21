from dataclasses import dataclass


@dataclass(slots=True)
class ProductionCalculationResult:
    work_order_no: str
    product_code: str
    op_no: str
    machine_code: str
    employee_code: str
    shift: str

    runtime_sec: float
    downtime_sec: float
    net_runtime_sec: float

    ok_qty: int
    ng_qty: int
    total_qty: int

    standard_cycle_time_sec: float
    actual_cycle_time_sec: float

    output_per_hour: float
    standard_output_per_hour: float

    yield_percent: float
    ng_percent: float
    performance_percent: float
    downtime_percent: float

    @property
    def runtime_min(self):
        return self.runtime_sec / 60

    @property
    def runtime_hour(self):
        return self.runtime_sec / 3600

    @property
    def downtime_min(self):
        return self.downtime_sec / 60

    @property
    def net_runtime_hour(self):
        return self.net_runtime_sec / 3600