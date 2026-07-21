import pandas as pd

from src.mapper.routing_mapper import RoutingMapper


dataframe = pd.DataFrame([
    {
        "Product Code": "P001",
        "OP No": "op10",
        "Sequence": 10,
        "OP Name": "CNC Turning",
        "Process Type": "Turning",
        "Machine Type": "",
        "Machine Code": "BL01",
        "Cycle Time Sec": 20,
        "Setup Time Min": 30,
        "Standard Output Hour": "",
        "Status": "ACTIVE",
    },
    {
        "Product Code": "P001",
        "OP No": "OP20",
        "Sequence": 20,
        "OP Name": "Robot Grinding",
        "Process Type": "Grinding",
        "Machine Type": "",
        "Machine Code": "BR01",
        "Cycle Time Sec": 40,
        "Setup Time Min": 20,
        "Standard Output Hour": "",
        "Status": "",
    },
])

records, errors = RoutingMapper.from_dataframe(
    dataframe
)

for record in records:
    print(record)

for error in errors:
    print(error)

assert len(records) == 2
assert len(errors) == 0

assert records[0]["data"]["op_no"] == "OP10"
assert records[0]["data"]["machine_type"] == "CNC"
assert (
    records[0]["data"]["standard_output_hour"]
    == 180.0
)

assert records[1]["data"]["machine_type"] == "ROBOT"
assert (
    records[1]["data"]["standard_output_hour"]
    == 90.0
)

print("RoutingMapper test passed.")