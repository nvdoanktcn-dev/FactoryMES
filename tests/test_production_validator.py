from datetime import datetime
from types import SimpleNamespace

from src.engine.production.production_validator import (
    ProductionValidator,
)


data = {
    "work_order_no": "wo001",
    "product_code": "p001",
    "op_no": "10",
    "machine_code": "bl01",
    "employee_code": "e001",
    "shift": "day",

    "start_time": datetime(
        2026,
        7,
        1,
        8,
        0,
    ),
    "finish_time": datetime(
        2026,
        7,
        1,
        9,
        0,
    ),

    "ok_qty": 100,
    "ng_qty": 2,
    "status": "COMPLETED",
}


work_order = SimpleNamespace(
    work_order_no="WO001",
    product_code="P001",
    status="RELEASED",
)


routing = SimpleNamespace(
    product_code="P001",
    op_no="OP10",
    machine_code="BL01",
    machine_type="CNC",
    cycle_time_sec=30,
    status="ACTIVE",
)


machine = SimpleNamespace(
    machine_code="BL01",
    machine_type="CNC",
    status="ACTIVE",
)


validator = ProductionValidator()

result = validator.validate(
    data=data,
    work_order=work_order,
    routing=routing,
    machine=machine,
    existing_record_hashes=set(),
)


print("=" * 80)
print("PRODUCTION VALIDATION")
print("=" * 80)

print("Valid:", result.is_valid)
print(
    "Hash:",
    result.normalized_data["record_hash"],
)
print(
    "Runtime:",
    result.normalized_data["run_time_sec"],
)

for issue in result.issues:
    print(
        issue.severity,
        issue.code,
        issue.field,
        issue.message,
    )


assert result.is_valid
assert (
    result.normalized_data["work_order_no"]
    == "WO001"
)
assert (
    result.normalized_data["product_code"]
    == "P001"
)
assert (
    result.normalized_data["op_no"]
    == "OP10"
)
assert (
    result.normalized_data["machine_code"]
    == "BL01"
)
assert (
    result.normalized_data["run_time_sec"]
    == 3600
)
assert len(
    result.normalized_data["record_hash"]
) == 64


duplicate_result = validator.validate(
    data=data,
    work_order=work_order,
    routing=routing,
    machine=machine,
    existing_record_hashes={
        result.normalized_data[
            "record_hash"
        ]
    },
)

assert duplicate_result.is_valid is False
assert any(
    issue.code
    == "DUPLICATE_PRODUCTION_LOG"
    for issue in duplicate_result.errors
)


wrong_machine = SimpleNamespace(
    machine_code="BR01",
    machine_type="ROBOT",
    status="ACTIVE",
)

invalid_machine_result = validator.validate(
    data={
        **data,
        "machine_code": "BR01",
    },
    work_order=work_order,
    routing=routing,
    machine=wrong_machine,
)

assert invalid_machine_result.is_valid is False

assert any(
    issue.code == "WRONG_ROUTING_MACHINE"
    for issue in invalid_machine_result.errors
)

assert any(
    issue.code == "MACHINE_TYPE_MISMATCH"
    for issue in invalid_machine_result.errors
)


print()
print(
    "ProductionValidator test passed."
)