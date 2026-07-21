from datetime import date

from src.engine.machine_runtime_engine import (
    MachineRuntimeEngine,
)
from src.engine.production_snapshot import (
    ProductionSnapshot,
)


snapshots = [
    ProductionSnapshot(
        work_order_no="WO001",
        product_code="P001",
        op_no="OP10",
        machine_code="BL01",
        operator_code="E001",
        production_date=date(
            2026,
            7,
            1,
        ),
        runtime_sec=1800,
        ok_qty=100,
        ng_qty=2,
    ),
    ProductionSnapshot(
        work_order_no="WO002",
        product_code="P002",
        op_no="OP10",
        machine_code="BL01",
        operator_code="E002",
        production_date=date(
            2026,
            7,
            1,
        ),
        runtime_sec=1200,
        ok_qty=60,
        ng_qty=1,
    ),
    ProductionSnapshot(
        work_order_no="WO003",
        product_code="P003",
        op_no="OP20",
        machine_code="BR01",
        operator_code="E003",
        production_date=date(
            2026,
            7,
            1,
        ),
        runtime_sec=2400,
        ok_qty=90,
        ng_qty=3,
    ),
    ProductionSnapshot(
        work_order_no="WO004",
        product_code="P004",
        op_no="OP10",
        machine_code="BL01",
        operator_code="E001",
        production_date=date(
            2026,
            7,
            2,
        ),
        runtime_sec=3600,
        ok_qty=200,
        ng_qty=4,
    ),
]


engine = MachineRuntimeEngine()

daily_results = engine.calculate_daily(
    snapshots
)

print("=" * 70)
print("MACHINE DAILY RUNTIME")
print("=" * 70)

for result in daily_results:
    print(
        result.production_date,
        result.machine_code,
        "Runtime Sec:",
        result.runtime_sec,
        "OK:",
        result.ok_qty,
        "NG:",
        result.ng_qty,
        "Yield:",
        round(
            result.yield_rate,
            2,
        ),
    )


bl01_day_1 = next(
    item
    for item in daily_results
    if (
        item.machine_code == "BL01"
        and item.production_date
        == date(2026, 7, 1)
    )
)

assert bl01_day_1.runtime_sec == 3000
assert bl01_day_1.ok_qty == 160
assert bl01_day_1.ng_qty == 3
assert bl01_day_1.snapshot_count == 2

machine_total = (
    engine.calculate_machine_total(
        snapshots,
        "BL01",
    )
)

print("=" * 70)
print("BL01 TOTAL")
print("=" * 70)
print(machine_total)

assert machine_total["runtime_sec"] == 6600
assert machine_total["ok_qty"] == 360
assert machine_total["ng_qty"] == 7
assert machine_total["day_count"] == 2

date_summary = (
    engine.calculate_date_summary(
        snapshots,
        date(2026, 7, 1),
    )
)

print("=" * 70)
print("DATE SUMMARY")
print("=" * 70)
print(
    "Machine Count:",
    date_summary["machine_count"],
)
print(
    "Runtime Sec:",
    date_summary["runtime_sec"],
)
print(
    "OK Qty:",
    date_summary["ok_qty"],
)
print(
    "NG Qty:",
    date_summary["ng_qty"],
)

assert date_summary["machine_count"] == 2
assert date_summary["runtime_sec"] == 5400
assert date_summary["ok_qty"] == 250
assert date_summary["ng_qty"] == 6

print()
print(
    "MachineRuntimeEngine test passed."
)