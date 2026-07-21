from datetime import date

from src.engine.machine_utilization_engine import (
    MachineUtilizationEngine,
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
        production_date=date(2026, 7, 1),
        runtime_sec=18900,
        ok_qty=500,
        ng_qty=5,
    ),
    ProductionSnapshot(
        work_order_no="WO002",
        product_code="P002",
        op_no="OP10",
        machine_code="BL01",
        operator_code="E002",
        production_date=date(2026, 7, 1),
        runtime_sec=9450,
        ok_qty=250,
        ng_qty=2,
    ),
    ProductionSnapshot(
        work_order_no="WO003",
        product_code="P003",
        op_no="OP20",
        machine_code="BR01",
        operator_code="E003",
        production_date=date(2026, 7, 1),
        runtime_sec=18450,
        ok_qty=300,
        ng_qty=4,
    ),
]


engine = MachineUtilizationEngine()

results = engine.calculate(
    snapshots
)

print("=" * 70)
print("MACHINE UTILIZATION")
print("=" * 70)

for result in results:
    print(
        result.production_date,
        result.machine_code,
        result.shift,
        "Runtime Hour:",
        round(result.runtime_hour, 2),
        "Available Hour:",
        round(result.available_hour, 2),
        "Utilization:",
        round(result.utilization_percent, 2),
        "%",
    )


bl01 = next(
    item
    for item in results
    if item.machine_code == "BL01"
)

assert bl01.runtime_sec == 28350
assert bl01.available_sec == 37800
assert round(
    bl01.utilization_percent,
    2,
) == 75.0

br01 = next(
    item
    for item in results
    if item.machine_code == "BR01"
)

assert br01.runtime_sec == 18450
assert round(
    br01.utilization_percent,
    2,
) == 48.81


summary = engine.calculate_machine_summary(
    snapshots,
    "BL01",
)

print("=" * 70)
print("BL01 SUMMARY")
print("=" * 70)
print(summary)

assert summary["runtime_sec"] == 28350
assert summary["available_sec"] == 37800
assert round(
    summary["utilization_percent"],
    2,
) == 75.0

print()
print(
    "MachineUtilizationEngine test passed."
)