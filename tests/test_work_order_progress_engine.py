from src.engine.last_operation_result import (
    LastOperationResult,
)
from src.engine.work_order_progress_engine import (
    WorkOrderProgressEngine,
)


class DummyWorkOrder:
    work_order_no = "WO001"
    plan_qty = 100
    status = "RELEASED"


last_result = LastOperationResult(
    work_order_no="WO001",
    product_code="P001",
    last_op="OP30",
    machine_code="BR01",
    runtime_sec=2900,
    ok_qty=97,
    ng_qty=1,
    snapshot_count=2,
)


engine = WorkOrderProgressEngine()

result = engine.calculate(
    work_order=DummyWorkOrder,
    last_operation_result=last_result,
)

print("=" * 70)
print("WORK ORDER PROGRESS")
print("=" * 70)

print("Work Order       :", result.work_order_no)
print("Plan Qty         :", result.plan_qty)
print("Completed Qty    :", result.completed_qty)
print("NG Qty           :", result.ng_qty)
print("Remaining Qty    :", result.remaining_qty)
print("Progress Percent :", round(
    result.progress_percent,
    2,
))
print("Current Status   :", result.current_status)
print("Suggested Status :", result.suggested_status)
print("Is Complete      :", result.is_complete)


assert result.plan_qty == 100
assert result.completed_qty == 97
assert result.remaining_qty == 3
assert round(
    result.progress_percent,
    2,
) == 97.0
assert result.suggested_status == "RUNNING"
assert result.is_complete is False


completed_result = LastOperationResult(
    work_order_no="WO001",
    product_code="P001",
    last_op="OP30",
    machine_code="BR01",
    runtime_sec=3000,
    ok_qty=100,
    ng_qty=1,
    snapshot_count=3,
)

completed_progress = engine.calculate(
    work_order=DummyWorkOrder,
    last_operation_result=completed_result,
)

assert completed_progress.remaining_qty == 0
assert completed_progress.progress_percent == 100.0
assert completed_progress.suggested_status == "COMPLETED"
assert completed_progress.is_complete is True

print()
print(
    "WorkOrderProgressEngine test passed."
)