import sys
from datetime import datetime
from types import SimpleNamespace
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
)

from src.ui.dashboard.dashboard_table_panel import DashboardTablePanel
from tests.qt_test_utils import get_test_app

def main():
    app = get_test_app()

    window = QWidget()
    window.setWindowTitle(
        "Dashboard Table Panel Test"
    )

    window.resize(
        1350,
        520,
    )

    layout = QVBoxLayout(window)

    panel = DashboardTablePanel()

    analytics = {
        "records": [
            SimpleNamespace(
                start_time=datetime(
                    2026,
                    7,
                    20,
                    8,
                    0,
                ),
                work_order_no="WO001",
                product_code="P001",
                op_no="OP10",
                machine_code="BL01",
                employee_code="E001",
                ok_qty=950,
                ng_qty=12,
                status="COMPLETED",
            ),
            SimpleNamespace(
                start_time=datetime(
                    2026,
                    7,
                    20,
                    9,
                    15,
                ),
                work_order_no="WO002",
                product_code="P002",
                op_no="OP20",
                machine_code="BR01",
                employee_code="E002",
                ok_qty=420,
                ng_qty=35,
                status="RUNNING",
            ),
        ],

        "import_history": [
            {
                "created_at":
                    datetime(
                        2026,
                        7,
                        20,
                        7,
                        30,
                    ),
                "module":
                    "WORK ORDER",
                "filename":
                    "work_order_20260720.xlsx",
                "total":
                    25,
                "created":
                    20,
                "updated":
                    5,
                "invalid":
                    0,
                "result":
                    "SUCCESS",
                "operator":
                    "ADMIN",
            },
            {
                "created_at":
                    datetime(
                        2026,
                        7,
                        20,
                        7,
                        45,
                    ),
                "module":
                    "ROUTING",
                "filename":
                    "routing.xlsx",
                "total":
                    15,
                "created":
                    12,
                "updated":
                    0,
                "invalid":
                    3,
                "result":
                    "PARTIAL",
                "operator":
                    "ADMIN",
            },
        ],

        "alarms": [
            {
                "created_at":
                    datetime(
                        2026,
                        7,
                        20,
                        10,
                        5,
                    ),
                "level":
                    "WARNING",
                "module":
                    "PRODUCTION",
                "code":
                    "LOW_YIELD",
                "message":
                    "Yield is below target.",
                "status":
                    "OPEN",
            },
            {
                "created_at":
                    datetime(
                        2026,
                        7,
                        20,
                        10,
                        15,
                    ),
                "level":
                    "ERROR",
                "module":
                    "MACHINE",
                "code":
                    "MACHINE_STOP",
                "message":
                    "Machine BL03 is stopped.",
                "status":
                    "OPEN",
            },
        ],
    }

    panel.update_data(analytics)

    layout.addWidget(panel)

    window.show()

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())