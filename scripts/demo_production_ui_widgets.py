import sys
from types import SimpleNamespace

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
)

from tests.qt_test_utils import get_test_app

app = get_test_app()

window = QWidget()
window.setWindowTitle(
    "Production UI Widgets Test"
)
window.resize(900, 620)

root_layout = QVBoxLayout(window)

date_layout = QHBoxLayout()

start_picker = DateTimePicker()
finish_picker = DateTimePicker()

date_layout.addWidget(start_picker)
date_layout.addWidget(finish_picker)

kpi_widget = ProductionKPIWidget()
warning_panel = WarningPanel()


calculation = SimpleNamespace(
    runtime_sec=7200,
    net_runtime_sec=6300,
    standard_cycle_time_sec=15,
    actual_cycle_time_sec=16.5,
    output_per_hour=218.18,
    yield_percent=94.5,
    performance_percent=90.91,
    ng_percent=5.5,
    downtime_percent=12.5,
)


class DummyIssue:
    def __init__(
        self,
        code,
        message,
    ):
        self.code = code
        self.message = message


class DummyEngineResult:
    errors = []

    warnings = [
        DummyIssue(
            "LOW_YIELD",
            "Yield is below target.",
        ),
        DummyIssue(
            "HIGH_NG_RATE",
            "NG Rate is above limit.",
        ),
    ]


kpi_widget.set_calculation(
    calculation
)

warning_panel.set_engine_result(
    DummyEngineResult()
)

root_layout.addLayout(date_layout)
root_layout.addWidget(kpi_widget)
root_layout.addWidget(warning_panel)

window.show()

sys.exit(app.exec())