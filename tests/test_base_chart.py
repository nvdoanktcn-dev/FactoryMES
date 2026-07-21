import sys

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
)

from src.dto.chart_data import BarChartData, ChartSeries
from src.ui.charts.bar_chart import BarChart
from tests.qt_test_utils import get_test_app

def main():
    app = get_test_app()

    window = QWidget()
    window.setWindowTitle("BaseChart Test")
    window.resize(1000, 650)

    root_layout = QVBoxLayout(window)

    chart = DemoLineChart(
        title="Daily Output Trend",
        subtitle="Factory Production Output",
    )

    initial_data = [
        {"label": "2026-07-01", "value": 1250},
        {"label": "2026-07-02", "value": 1600},
        {"label": "2026-07-03", "value": 1480},
        {"label": "2026-07-04", "value": 1920},
        {"label": "2026-07-05", "value": 2100},
    ]
    chart.set_data(initial_data)

    button_layout = QHBoxLayout()

    btn_clear = QPushButton("Clear")
    btn_reload = QPushButton("Reload")

    def clear_chart():
        chart.clear_chart()

    def reload_chart():
        chart.set_data(
            [
                {"label": "2026-07-06", "value": 1800},
                {"label": "2026-07-07", "value": 2200},
                {"label": "2026-07-08", "value": 2050},
            ]
        )

    btn_clear.clicked.connect(clear_chart)
    btn_reload.clicked.connect(reload_chart)

    button_layout.addWidget(btn_clear)
    button_layout.addWidget(btn_reload)
    button_layout.addStretch()

    root_layout.addWidget(chart, 1)
    root_layout.addLayout(button_layout)

    window.show()
    return app.exec()


def main():
    app = get_test_app()

    chart = BarChart(
        title="Machine Output",
    )

    # chart.load_data(...)

    chart.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())