import pandas as pd

from src.mapper.work_order_mapper import WorkOrderMapper


dataframe = pd.DataFrame([
    {
        "Work Order No": " wo001 ",
        "Product Code": " p001 ",
        "Plan Qty": 100,
        "Completed Qty": "",
        "NG Qty": "",
        "Start Date": "01/07/2026",
        "Due Date": "31/07/2026",
        "Finish Date": "",
        "Status": "planned",
        "Priority": "normal",
        "Remark": "Test Work Order 1",
    },
    {
        "Work Order No": "WO002",
        "Product Code": "P001",
        "Plan Qty": "250",
        "Completed Qty": 25,
        "NG Qty": 2,
        "Start Date": "2026-07-10",
        "Due Date": "2026-08-10",
        "Finish Date": "",
        "Status": "đã phát hành",
        "Priority": "cao",
        "Remark": "",
    },
])


records, errors = WorkOrderMapper.from_dataframe(
    dataframe
)

print("=" * 70)
print("WORK ORDER RECORDS")
print("=" * 70)

for record in records:
    print(record)

print("=" * 70)
print("ERRORS")
print("=" * 70)

for error in errors:
    print(error)


assert len(records) == 2
assert len(errors) == 0

first = records[0]["data"]
second = records[1]["data"]

assert first["work_order_no"] == "WO001"
assert first["product_code"] == "P001"
assert first["plan_qty"] == 100
assert first["completed_qty"] == 0
assert first["ng_qty"] == 0
assert first["status"] == "PLANNED"
assert first["priority"] == "NORMAL"

assert second["work_order_no"] == "WO002"
assert second["plan_qty"] == 250
assert second["completed_qty"] == 25
assert second["ng_qty"] == 2
assert second["status"] == "RELEASED"
assert second["priority"] == "HIGH"

print("WorkOrderMapper test passed.")