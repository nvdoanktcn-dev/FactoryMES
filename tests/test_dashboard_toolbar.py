import sys
from types import SimpleNamespace

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
)

from src.ui.dashboard.dashboard_toolbar import DashboardToolbar

from tests.qt_test_utils import get_test_app

def main():
    app = get_test_app()

    window = QWidget()
    window.setWindowTitle(
        "Dashboard Toolbar Test"
    )
    window.resize(
        1500,
        160,
    )

    layout = QVBoxLayout(window)

    toolbar = DashboardToolbar()

    toolbar.set_machines([
        SimpleNamespace(
            machine_code="BL01",
            machine_name="CNC Lathe 01",
        ),
        SimpleNamespace(
            machine_code="BR01",
            machine_name="Robot 01",
        ),
    ])

    toolbar.set_work_orders([
        SimpleNamespace(
            work_order_no="WO001",
            product_code="P001",
        ),
        SimpleNamespace(
            work_order_no="WO002",
            product_code="P002",
        ),
    ])

    toolbar.set_employees([
        SimpleNamespace(
            employee_code="E001",
            employee_name="Operator One",
        ),
    ])

    toolbar.set_products([
        SimpleNamespace(
            product_code="P001",
            product_name_vi="Product One",
        ),
    ])

    def on_refresh(request):
        print("=" * 70)
        print("DASHBOARD REQUEST")
        print("=" * 70)

        print(
            "start_date:",
            request.start_date,
        )

        print(
            "end_date:",
            request.end_date,
        )

        print(
            "shift:",
            request.shift,
        )

        print(
            "machine_code:",
            request.machine_code,
        )

        print(
            "work_order_no:",
            request.work_order_no,
        )

        print(
            "employee_code:",
            request.employee_code,
        )

        print(
            "product_code:",
            request.product_code,
        )

        print(
            "auto_refresh:",
            request.auto_refresh,
        )

        print(
            "refresh_interval:",
            request.refresh_interval,
        )

    toolbar.refresh_requested.connect(
        on_refresh
    )

    layout.addWidget(toolbar)

    window.show()

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())