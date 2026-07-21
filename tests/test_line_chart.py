import sys

from PySide6.QtWidgets import QWidget
from src.ui.charts.line_chart import LineChart
from src.dto.chart_data import (
    ChartSeries,
    LineChartData,
)

from tests.qt_test_utils import get_test_app

app = get_test_app()

chart = LineChart(
    title="Daily Output Trend",
)

chart.resize(
    900,
    500,
)

chart.load_data(
    LineChartData(
        title="Daily Output",
        labels=[
            "01",
            "02",
            "03",
            "04",
            "05",
        ],
        series=[
            ChartSeries(
                name="OK",
                values=[
                    100,
                    150,
                    120,
                    180,
                    210,
                ],
                unit="PCS",
            ),
            ChartSeries(
                name="NG",
                values=[
                    8,
                    5,
                    12,
                    6,
                    4,
                ],
                unit="PCS",
            ),
            ChartSeries(
                name="Yield",
                values=[
                    92,
                    97,
                    90,
                    96,
                    98,
                ],
                unit="%",
            ),
        ],
        x_label="Day",
        y_label="Value",
    )
)

def main():
    app = get_test_app()

    # tạo chart
    # load_data(...)
    # chart.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())