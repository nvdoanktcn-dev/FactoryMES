from datetime import date

from src.engine.machine_utilization_result import (
    MachineUtilizationResult,
)
from src.engine.oee_engine import OEEEngine


utilization_result = MachineUtilizationResult(
    machine_code="BL01",
    production_date=date(
        2026,
        7,
        1,
    ),
    shift="DAY",

    # 10,5 giờ khả dụng
    available_sec=37800,

    # Máy chạy 7,875 giờ
    runtime_sec=28350,

    ok_qty=900,
    ng_qty=20,
    snapshot_count=3,

    # Runtime / Available = 75%
    utilization_percent=75.0,
)


engine = OEEEngine()

result = engine.calculate(
    utilization_result=utilization_result,

    # Chu kỳ chuẩn 25 giây/PCS
    ideal_cycle_time_sec=25,
)


print("=" * 70)
print("OEE RESULT")
print("=" * 70)

print(
    "Machine      :",
    result.machine_code,
)
print(
    "Date         :",
    result.production_date,
)
print(
    "Shift        :",
    result.shift,
)
print(
    "Availability :",
    round(
        result.availability_percent,
        2,
    ),
    "%",
)
print(
    "Performance  :",
    round(
        result.performance_percent,
        2,
    ),
    "%",
)
print(
    "Quality      :",
    round(
        result.quality_percent,
        2,
    ),
    "%",
)
print(
    "OEE          :",
    round(
        result.oee_percent,
        2,
    ),
    "%",
)
print(
    "Ideal Output :",
    round(
        result.ideal_output_qty,
        2,
    ),
)
print(
    "Actual Total :",
    result.total_qty,
)


assert round(
    result.availability_percent,
    2,
) == 75.0

# 25 × 920 / 28350 × 100
assert round(
    result.performance_percent,
    2,
) == 81.13

# 900 / 920 × 100
assert round(
    result.quality_percent,
    2,
) == 97.83

assert abs(
    result.oee_percent - 59.53
) < 0.02

assert result.total_qty == 920


print()
print("OEEEngine test passed.")