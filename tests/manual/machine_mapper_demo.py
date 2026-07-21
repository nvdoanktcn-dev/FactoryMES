import pandas as pd

from src.mapper.machine_mapper import MachineMapper


dataframe = pd.DataFrame([
    {
        "Machine Code": " bl01 ",
        "Machine Name": "CNC Lathe 01",
        "Machine Type": "",
        "Department": "CNC",
        "Status": "active",
        "Remark": "Test CNC machine",
    },
    {
        "Machine Code": "BR01",
        "Machine Name": "Robot Grinding 01",
        "Machine Type": "",
        "Department": "ROBOT",
        "Status": "",
        "Remark": "",
    },
    {
        "Machine Code": "ASK01",
        "Machine Name": "ASK Robot 01",
        "Machine Type": "robot",
        "Department": "ROBOT",
        "Status": "hoạt động",
        "Remark": "",
    },
])

records, errors = MachineMapper.from_dataframe(
    dataframe
)

print("=" * 70)
print("MACHINE RECORDS")
print("=" * 70)

for record in records:
    print(
        "Excel row:",
        record["excel_row"],
        "| Data:",
        record["data"],
    )

print("=" * 70)
print("ERRORS")
print("=" * 70)

for error in errors:
    print(error)

assert len(records) == 3
assert len(errors) == 0

assert (
    records[0]["data"]["machine_code"]
    == "BL01"
)
assert (
    records[0]["data"]["machine_type"]
    == "CNC"
)

assert (
    records[1]["data"]["machine_type"]
    == "ROBOT"
)
assert (
    records[2]["data"]["machine_type"]
    == "ROBOT"
)

assert (
    records[2]["data"]["status"]
    == "ACTIVE"
)

print("MachineMapper test passed.")