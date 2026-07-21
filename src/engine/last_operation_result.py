from dataclasses import dataclass


@dataclass(slots=True)
class LastOperationResult:
    """
    Kết quả phân tích sản lượng tại OP cuối của một Work Order.
    """

    work_order_no: str
    product_code: str
    last_op: str
    machine_code: str
    runtime_sec: float
    ok_qty: int
    ng_qty: int
    snapshot_count: int = 0

    @property
    def completed_qty(self):
        return self.ok_qty

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
    def runtime_hour(self):
        return self.runtime_sec / 3600