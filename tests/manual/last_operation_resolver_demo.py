from datetime import date

from src.engine.last_operation_resolver import (
    LastOperationResolver,
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
        work_order_no="WO001",
        product_code="P001",
        op_no="OP20",
        machine_code="BL02",
        operator_code="E002",
        production_date=date(
            2026,
            7,
            1,
        ),
        runtime_sec=2400,
        ok_qty=98,
        ng_qty=1,
    ),
    ProductionSnapshot(
        work_order_no="WO001",
        product_code="P001",
        op_no="OP30",
        machine_code="BR01",
        operator_code="E003",
        production_date=date(
            2026,
            7,
            1,
        ),
        runtime_sec=1500,
        ok_qty=50,
        ng_qty=1,
    ),
    ProductionSnapshot(
        work_order_no="WO001",
        product_code="P001",
        op_no="OP30",
        machine_code="BR01",
        operator_code="E004",
        production_date=date(
            2026,
            7,
            2,
        ),
        runtime_sec=1400,
        ok_qty=47,
        ng_qty=0,
    ),
    ProductionSnapshot(
        work_order_no="WO002",
        product_code="P002",
        op_no="OP30",
        machine_code="BR02",
        operator_code="E005",
        production_date=date(
            2026,
            7,
            1,
        ),
        runtime_sec=1200,
        ok_qty=200,
        ng_qty=2,
    ),
]


resolver = LastOperationResolver()

result = resolver.resolve(
    work_order_no="WO001",
    last_operation="OP30",
    snapshots=snapshots,
)

print("=" * 70)
print("LAST OPERATION RESULT")
print("=" * 70)

print("Work Order     :", result.work_order_no)
print("Product        :", result.product_code)
print("Last OP        :", result.last_op)
print("Machine        :", result.machine_code)
print("Runtime Sec    :", result.runtime_sec)
print("OK Qty         :", result.ok_qty)
print("NG Qty         :", result.ng_qty)
print("Completed Qty  :", result.completed_qty)
print("Total Qty      :", result.total_qty)
print("Yield Rate     :", round(
    result.yield_rate,
    2,
))
print("Snapshot Count :", result.snapshot_count)


assert result.work_order_no == "WO001"
assert result.product_code == "P001"
assert result.last_op == "OP30"
assert result.machine_code == "BR01"

assert result.ok_qty == 97
assert result.ng_qty == 1
assert result.completed_qty == 97

assert result.runtime_sec == 2900
assert result.snapshot_count == 2

assert round(
    result.yield_rate,
    2,
) == 98.98

print()
print(
    "LastOperationResolver test passed."
)