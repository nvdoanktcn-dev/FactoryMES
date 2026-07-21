from src.services.work_order_progress_service import (
    WorkOrderProgressService,
)


WORK_ORDER_NO = "WO202607001"


service = WorkOrderProgressService()

calculation = service.calculate_progress(
    WORK_ORDER_NO
)

last_result = calculation[
    "last_operation_result"
]
progress = calculation[
    "progress_result"
]

print("=" * 70)
print("WORK ORDER PROGRESS SERVICE")
print("=" * 70)

print("Work Order       :", progress.work_order_no)
print("Last OP          :", last_result.last_op)
print("Last OP OK       :", last_result.ok_qty)
print("Last OP NG       :", last_result.ng_qty)
print("Plan Qty         :", progress.plan_qty)
print("Completed Qty    :", progress.completed_qty)
print("Remaining Qty    :", progress.remaining_qty)
print(
    "Progress Percent :",
    round(progress.progress_percent, 2),
)
print("Current Status   :", progress.current_status)
print("Suggested Status :", progress.suggested_status)
print("Snapshot Count   :", last_result.snapshot_count)

assert progress.work_order_no == WORK_ORDER_NO

print()
print(
    "WorkOrderProgressService calculation passed."
)

updated_progress = service.update_progress(
    WORK_ORDER_NO
)

print("=" * 70)
print("DATABASE UPDATE")
print("=" * 70)

print(
    "Completed Qty    :",
    updated_progress.completed_qty,
)
print(
    "NG Qty           :",
    updated_progress.ng_qty,
)
print(
    "Suggested Status :",
    updated_progress.suggested_status,
)

print(
    "WorkOrderProgressService update passed."
)