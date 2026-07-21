import sys

from tests.qt_test_utils import get_test_app
from src.ui.pages.dashboard_page import DashboardPage

app = get_test_app()


def main():
    page = DashboardPage()
    page.resize(1600, 950)
    page.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())