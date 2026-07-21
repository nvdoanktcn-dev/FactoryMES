from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class OEEResult:
    """
    Kết quả OEE của một máy trong một ngày và ca.
    """

    machine_code: str
    production_date: date
    shift: str

    available_sec: float
    runtime_sec: float
    ideal_cycle_time_sec: float

    ok_qty: int
    ng_qty: int
    total_qty: int

    availability_percent: float
    performance_percent: float
    quality_percent: float
    oee_percent: float

    @property
    def available_hour(self):
        return self.available_sec / 3600

    @property
    def runtime_hour(self):
        return self.runtime_sec / 3600

    @property
    def ideal_output_qty(self):
        if self.ideal_cycle_time_sec <= 0:
            return 0.0

        return (
            self.runtime_sec
            / self.ideal_cycle_time_sec
        )

    @property
    def production_loss_qty(self):
        return max(
            self.ideal_output_qty - self.total_qty,
            0.0,
        )