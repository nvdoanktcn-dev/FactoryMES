import sys

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
)

from src.ui.dashboard.dashboard_kpi_panel import DashboardKPIPanel
from tests.qt_test_utils import get_test_app

def main():
    app = get_test_app()

    window = QWidget()
    window.setWindowTitle("Dashboard KPI Panel Test")
    window.resize(1300, 420)

    layout = QVBoxLayout(window)

    panel = DashboardKPIPanel()

    analytics = {
        ...
    }

    panel.update_data(analytics)

    layout.addWidget(panel)

    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())