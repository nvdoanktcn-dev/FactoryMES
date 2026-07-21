from datetime import date, datetime

from src.engine.production_snapshot_engine import (
    ProductionSnapshotEngine,
)


class DummyLog:

    work_order_no = "WO001"

    product_code = "P001"

    op_no = "OP10"

    machine_code = "BL01"

    operator_code = "EMP001"

    production_date = date(
        2026,
        7,
        1,
    )

    start_time = datetime(
        2026,
        7,
        1,
        8,
        0,
    )

    end_time = datetime(
        2026,
        7,
        1,
        8,
        35,
    )

    ok_qty = 100

    ng_qty = 2


snapshot = (
    ProductionSnapshotEngine
    .create_snapshot(
        DummyLog
    )
)

print(snapshot)

assert snapshot.runtime_sec == 2100

assert snapshot.total_qty == 102

assert round(
    snapshot.yield_rate,
    2,
) == 98.04

assert round(
    snapshot.output_per_hour,
    2,
) == 171.43

print()

print(
    "ProductionSnapshot test passed."
)