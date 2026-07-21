from src.ui.charts.chart_utils import (
    ChartUtils,
)


print("=" * 70)
print("CHART UTILS")
print("=" * 70)


values = [
    10,
    20,
    30,
    40,
]


assert ChartUtils.total(values) == 100
assert ChartUtils.average(values) == 25
assert ChartUtils.minimum(values) == 10
assert ChartUtils.maximum(values) == 40
assert ChartUtils.median_value(values) == 25


axis_max = ChartUtils.calculate_axis_max(
    values
)

print("Axis Max:", axis_max)

assert axis_max >= 40


percentages = (
    ChartUtils.calculate_percentages(
        [60, 30, 10]
    )
)

print("Percentages:", percentages)

assert [
    round(value, 2)
    for value in percentages
] == [
    60.0,
    30.0,
    10.0,
]


cumulative = (
    ChartUtils
    .calculate_cumulative_percent(
        [60, 30, 10]
    )
)

print(
    "Cumulative Percent:",
    cumulative,
)

assert [
    round(value, 2)
    for value in cumulative
] == [
    60.0,
    90.0,
    100.0,
]


pareto = ChartUtils.pareto_data(
    labels=[
        "P003",
        "P001",
        "P002",
    ],
    values=[
        10,
        60,
        30,
    ],
)

print("Pareto:", pareto)

assert pareto["labels"] == [
    "P001",
    "P002",
    "P003",
]

assert pareto["values"] == [
    60.0,
    30.0,
    10.0,
]


moving_average = (
    ChartUtils.moving_average(
        [10, 20, 30, 40],
        window_size=3,
    )
)

print(
    "Moving Average:",
    moving_average,
)

assert [
    round(value, 2)
    for value in moving_average
] == [
    10.0,
    15.0,
    20.0,
    30.0,
]


growth = ChartUtils.growth_rates(
    [100, 120, 90]
)

print("Growth Rates:", growth)

assert round(
    growth[1],
    2,
) == 20.0

assert round(
    growth[2],
    2,
) == -25.0


trend = ChartUtils.linear_trend(
    [10, 20, 30, 40]
)

print("Linear Trend:", trend)

assert [
    round(value, 2)
    for value in trend
] == [
    10.0,
    20.0,
    30.0,
    40.0,
]


ranking = ChartUtils.rank_values(
    [100, 80, 100, 40]
)

print("Ranking:", ranking)

assert ranking == [
    1,
    2,
    1,
    3,
]


print()
print(
    "ChartUtils test passed."
)