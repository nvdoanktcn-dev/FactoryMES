from src.ui.charts.chart_theme import (
    ChartTheme,
)

print("=" * 60)

print(
    ChartTheme.color_for_series(
        "OK"
    )
)

print(
    ChartTheme.color_for_series(
        "NG"
    )
)

print(
    ChartTheme.color_for_series(
        "Yield"
    )
)

print(
    ChartTheme.color_for_series(
        "OEE"
    )
)

print(
    ChartTheme.color_for_series(
        "Unknown"
    )
)

assert (
    ChartTheme.color_for_series(
        "OK"
    )
    == ChartTheme.OK_COLOR
)

assert (
    ChartTheme.color_for_series(
        "NG"
    )
    == ChartTheme.NG_COLOR
)

assert (
    ChartTheme.color_for_series(
        "Yield"
    )
    == ChartTheme.YIELD_COLOR
)

assert (
    ChartTheme.color_for_series(
        "Unknown"
    )
    == ChartTheme.DEFAULT_COLOR
)

print()
print("ChartTheme OK")