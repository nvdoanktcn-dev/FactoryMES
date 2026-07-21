from matplotlib.figure import Figure

from src.dto.chart_data import (
    ChartSeries,
    LineChartData,
)
from src.ui.charts.renderers.line_renderer import (
    LineRenderer,
)


figure = Figure()

axes = figure.add_subplot(
    111
)


data = LineChartData(
    title="Daily Production",
    labels=[
        "01",
        "02",
        "03",
        "04",
    ],
    series=[
        ChartSeries(
            name="OK",
            values=[
                100,
                120,
                140,
                160,
            ],
            unit="PCS",
        ),
        ChartSeries(
            name="NG",
            values=[
                5,
                4,
                8,
                3,
            ],
            unit="PCS",
        ),
    ],
    x_label="Day",
    y_label="Output",
    unit="PCS",
    show_legend=True,
    show_markers=True,
)


LineRenderer.render(
    axes=axes,
    data=data,
)


assert len(
    axes.lines
) == 2

assert (
    axes.get_title()
    == "Daily Production"
)

assert (
    axes.get_xlabel()
    == "Day"
)

assert (
    axes.get_ylabel()
    == "Output (PCS)"
)


legend = axes.get_legend()

assert legend is not None


print("=" * 70)
print("LINE RENDERER")
print("=" * 70)

print(
    "Lines:",
    len(axes.lines),
)

print(
    "Title:",
    axes.get_title(),
)

print(
    "X Label:",
    axes.get_xlabel(),
)

print(
    "Y Label:",
    axes.get_ylabel(),
)

print()
print(
    "LineRenderer test passed."
)