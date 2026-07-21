import sys

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
)

from src.ui.dashboard.dashboard_status_panel import DashboardStatusPanel
from src.services.system_status_service import SystemStatusService
from tests.qt_test_utils import get_test_app

def main():
    app = get_test_app()

    window = QWidget()
    window.setWindowTitle("Dashboard Status Panel Test")
    window.resize(900, 360)

    layout = QVBoxLayout(window)

    panel = DashboardStatusPanel()

    status = SystemStatusService().build_status()
    panel.update_status(status)

    layout.addWidget(panel)

    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())