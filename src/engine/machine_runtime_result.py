from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class MachineRuntimeResult:
    machine_code: str
    production_date: date

    runtime_sec: float
    ok_qty: int
    ng_qty: int
    snapshot_count: int

    @property
    def runtime_min(self):
        return self.runtime_sec / 60

    @property
    def runtime_hour(self):
        return self.runtime_sec / 3600

    @property
    def total_qty(self):
        return self.ok_qty + self.ng_qty

    @property
    def yield_rate(self):
        if self.total_qty <= 0:
            return 0.0

        return (
            self.ok_qty
            / self.total_qty
        ) * 100

    @property
    def output_per_hour(self):
        if self.runtime_sec <= 0:
            return 0.0

        return (
            self.ok_qty
            * 3600
            / self.runtime_sec
        )