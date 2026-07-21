from datetime import datetime
from types import SimpleNamespace

from src.engine.production.production_engine import (
    ProductionEngine,
)


data = {
    "work_order_no": "WO001",
    "product_code": "P001",
    "op_no": "OP10",
    "machine_code": "BL01",
    "employee_code": "E001",
    "shift": "DAY",

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
        10,
        0,
    ),

    # Runtime sẽ tự tính = 7200 sec
    "run_time_sec": 0,

    # Downtime 20 phút
    "downtime_min": 20,

    "ok_qty": 340,
    "ng_qty": 60,

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
    cycle_time_sec=15,
    status="ACTIVE",
)


machine = SimpleNamespace(
    machine_code="BL01",
    machine_type="CNC",
    status="ACTIVE",
)


engine = ProductionEngine()

result = engine.process(
    data=data,
    work_order=work_order,
    routing=routing,
    machine=machine,
)


print("=" * 90)
print("PRODUCTION ENGINE")
print("=" * 90)

print("Valid       :", result.is_valid)
print("Can Save    :", result.can_save)
print("Has Warning :", result.has_warnings)


for error in result.errors:
    print(
        "ERROR:",
        error.code,
        error.message,
    )


for warning in result.warnings:
    print(
        "WARNING:",
        warning.code,
        warning.message,
    )


assert result.is_valid
assert result.can_save
assert result.calculation is not None

calculation = result.calculation

print()
print("Runtime Sec      :", calculation.runtime_sec)
print("Downtime Sec     :", calculation.downtime_sec)
print("Net Runtime Sec  :", calculation.net_runtime_sec)
print("Total Qty        :", calculation.total_qty)
print(
    "Actual Cycle     :",
    round(
        calculation.actual_cycle_time_sec,
        2,
    ),
)
print(
    "Performance      :",
    round(
        calculation.performance_percent,
        2,
    ),
)
print(
    "Yield            :",
    round(
        calculation.yield_percent,
        2,
    ),
)
print(
    "NG Rate          :",
    round(
        calculation.ng_percent,
        2,
    ),
)
print(
    "Downtime Rate    :",
    round(
        calculation.downtime_percent,
        2,
    ),
)


assert calculation.runtime_sec == 7200
assert calculation.downtime_sec == 1200
assert calculation.net_runtime_sec == 6000
assert calculation.total_qty == 400

assert round(
    calculation.actual_cycle_time_sec,
    2,
) == 15.0

assert round(
    calculation.performance_percent,
    2,
) == 100.0

assert round(
    calculation.yield_percent,
    2,
) == 85.0

assert round(
    calculation.ng_percent,
    2,
) == 15.0

assert round(
    calculation.downtime_percent,
    2,
) == 16.67


warning_codes = {
    warning.code
    for warning in result.warnings
}

assert "LOW_YIELD" in warning_codes
assert "HIGH_NG_RATE" in warning_codes
assert "HIGH_DOWNTIME" in warning_codes


print()
print(
    "Valid ProductionEngine test passed."
)


# ==============================================================
# Invalid case
# ==============================================================

invalid_result = engine.process(
    data={
        **data,
        "machine_code": "BR01",
    },
    work_order=work_order,
    routing=routing,
    machine=SimpleNamespace(
        machine_code="BR01",
        machine_type="ROBOT",
        status="ACTIVE",
    ),
)


assert invalid_result.is_valid is False
assert invalid_result.can_save is False
assert invalid_result.calculation is None

invalid_codes = {
    error.code
    for error in invalid_result.errors
}

assert "WRONG_ROUTING_MACHINE" in invalid_codes
assert "MACHINE_TYPE_MISMATCH" in invalid_codes


print(
    "Invalid ProductionEngine test passed."
)

print()
print(
    "ProductionEngine test passed."
)