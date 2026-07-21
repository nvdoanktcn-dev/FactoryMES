from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class MachineUtilizationResult:
    machine_code: str
    production_date: date
    shift: str

    runtime_sec: float
    available_sec: float
    utilization_percent: float

    ok_qty: int
    ng_qty: int
    snapshot_count: int

    @property
    def runtime_hour(self):
        return self.runtime_sec / 3600

    @property
    def available_hour(self):
        return self.available_sec / 3600

    @property
    def idle_sec(self):
        return max(
            self.available_sec - self.runtime_sec,
            0.0,
        )

    @property
    def idle_hour(self):
        return self.idle_sec / 3600