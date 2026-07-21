from src.ui.charts.chart_formatter import (
    ChartFormatter,
)

print("=" * 60)

print(
    ChartFormatter.format_qty(
        15230
    )
)

print(
    ChartFormatter.format_percent(
        98.7634
    )
)

print(
    ChartFormatter.format_runtime(
        12800
    )
)

print(
    ChartFormatter.format_compact(
        1234567
    )
)

print(
    ChartFormatter.auto(
        95.34,
        "%",
    )
)

print(
    ChartFormatter.auto(
        1000,
        "PCS",
    )
)

assert (
    ChartFormatter.format_qty(
        1000
    )
    == "1,000 PCS"
)

assert (
    ChartFormatter.format_runtime(
        3661
    )
    == "1h 1m 1s"
)

assert (
    ChartFormatter.format_compact(
        1200000
    )
    == "1.20M"
)

print()
print(
    "ChartFormatter OK"
)