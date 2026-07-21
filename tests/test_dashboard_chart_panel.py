import sys

from tests.qt_test_utils import get_test_app
from src.ui.dashboard.dashboard_chart_panel import DashboardChartPanel


def main():
    app = get_test_app()

    panel = DashboardChartPanel()
    panel.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())