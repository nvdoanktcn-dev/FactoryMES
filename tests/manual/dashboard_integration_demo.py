import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget,
    QStackedWidget,
    QStackedWidget,
)
from src.ui.dashboard.dashboard_page import DashboardPage
from src.ui.navigation.navigation_manager import NavigationManager
from tests.qt_test_utils import get_test_app

app = get_test_app()

stack = QStackedWidget()

manager = NavigationManager(
    stack
)

manager.pages = {}

dashboard = DashboardPage()

manager._register_page(
    "Dashboard",
    dashboard,
)

manager.navigate(
    "Dashboard"
)


assert (
    "Dashboard"
    in manager.pages
)

assert (
    manager.pages[
        "Dashboard"
    ]
    is dashboard
)

assert (
    stack.currentWidget()
    is dashboard
)

assert dashboard.controller is not None

assert (
    dashboard.controller.facade
    is not None
)

assert (
    dashboard.toolbar
    is not None
)

assert (
    dashboard.kpi_panel
    is not None
)

assert (
    dashboard.chart_panel
    is not None
)

assert (
    dashboard.table_panel
    is not None
)

assert (
    dashboard.status_panel
    is not None
)


print("=" * 80)
print("DASHBOARD INTEGRATION")
print("=" * 80)

print(
    "Dashboard registered:",
    True,
)

print(
    "Controller:",
    type(
        dashboard.controller
    ).__name__,
)

print(
    "Facade:",
    type(
        dashboard.controller.facade
    ).__name__,
)

print(
    "Cache:",
    dashboard.controller
    .cache_statistics(),
)

print()
print(
    "Dashboard integration test passed."
)


def main():
    app = get_test_app()

    dashboard = DashboardPage()

    # Khởi tạo NavigationManager tại đây
    # manager = NavigationManager(...)

    dashboard.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())