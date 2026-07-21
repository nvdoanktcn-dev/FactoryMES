from types import SimpleNamespace

from src.engine.production.production_calculator import (
    ProductionCalculator,
)


data = {
    "work_order_no": "WO001",
    "product_code": "P001",
    "op_no": "OP10",
    "machine_code": "BL01",
    "employee_code": "E001",
    "shift": "DAY",

    # 2 giờ
    "run_time_sec": 7200,

    # Dừng 20 phút
    "downtime_min": 20,

    "ok_qty": 380,
    "ng_qty": 20,
}


routing = SimpleNamespace(
    cycle_time_sec=15,
)


calculator = ProductionCalculator()

result = calculator.calculate(
    data=data,
    routing=routing,
)


print("=" * 80)
print("PRODUCTION CALCULATION")
print("=" * 80)

print("Runtime Sec        :", result.runtime_sec)
print("Downtime Sec       :", result.downtime_sec)
print("Net Runtime Sec    :", result.net_runtime_sec)
print("OK Qty             :", result.ok_qty)
print("NG Qty             :", result.ng_qty)
print("Total Qty          :", result.total_qty)
print(
    "Standard Cycle     :",
    round(result.standard_cycle_time_sec, 2),
)
print(
    "Actual Cycle       :",
    round(result.actual_cycle_time_sec, 2),
)
print(
    "Output/Hour        :",
    round(result.output_per_hour, 2),
)
print(
    "Standard Output/H  :",
    round(result.standard_output_per_hour, 2),
)
print(
    "Yield              :",
    round(result.yield_percent, 2),
    "%",
)
print(
    "NG Rate            :",
    round(result.ng_percent, 2),
    "%",
)
print(
    "Performance        :",
    round(result.performance_percent, 2),
    "%",
)
print(
    "Downtime Rate      :",
    round(result.downtime_percent, 2),
    "%",
)


assert result.runtime_sec == 7200
assert result.downtime_sec == 1200
assert result.net_runtime_sec == 6000

assert result.ok_qty == 380
assert result.ng_qty == 20
assert result.total_qty == 400

assert round(
    result.standard_cycle_time_sec,
    2,
) == 15.0

assert round(
    result.actual_cycle_time_sec,
    2,
) == 15.0

assert round(
    result.output_per_hour,
    2,
) == 240.0

assert round(
    result.standard_output_per_hour,
    2,
) == 240.0

assert round(
    result.yield_percent,
    2,
) == 95.0

assert round(
    result.ng_percent,
    2,
) == 5.0

assert round(
    result.performance_percent,
    2,
) == 100.0

assert round(
    result.downtime_percent,
    2,
) == 16.67


print()
print(
    "ProductionCalculator test passed."
)
