from datetime import date, timedelta

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.services.manufacturing_analytics_service import (
    ManufacturingAnalyticsService,
)
from src.ui.widgets.dashboard_kpi_card import (
    DashboardKPICard,
)
from src.ui.widgets.dashboard_table import (
    DashboardTable,
)


class DashboardPage(QWidget):
    """
    FactoryMES Dashboard V3.

    Dashboard không tự tính nghiệp vụ.
    Toàn bộ KPI được lấy từ
    ManufacturingAnalyticsService.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.analytics_service = (
            ManufacturingAnalyticsService()
        )

        today = date.today()

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat(
            "yyyy-MM-dd"
        )
        self.start_date.setDate(
            QDate(
                today.year,
                today.month,
                1,
            )
        )

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat(
            "yyyy-MM-dd"
        )
        self.end_date.setDate(
            QDate.currentDate()
        )

        self.btn_today = QPushButton(
            "Today"
        )

        self.btn_month = QPushButton(
            "This Month"
        )

        self.btn_refresh = QPushButton(
            "Refresh"
        )

        self.card_output = DashboardKPICard(
            "Total Output",
            "0",
            "PCS",
        )

        self.card_ok = DashboardKPICard(
            "OK Quantity",
            "0",
            "PCS",
        )

        self.card_ng = DashboardKPICard(
            "NG Quantity",
            "0",
            "PCS",
        )

        self.card_yield = DashboardKPICard(
            "Yield",
            "0",
            "%",
        )

        self.card_runtime = DashboardKPICard(
            "Runtime",
            "0",
            "Hour",
        )

        self.card_downtime = DashboardKPICard(
            "Downtime",
            "0",
            "Hour",
        )

        self.card_output_hour = DashboardKPICard(
            "Output / Hour",
            "0",
            "PCS/H",
        )

        self.card_oee = DashboardKPICard(
            "OEE",
            "0",
            "%",
        )

        self.machine_table = DashboardTable([
            "Machine",
            "Runtime H",
            "OK",
            "NG",
            "Yield %",
            "Output/H",
        ])

        self.employee_table = DashboardTable([
            "Employee",
            "Runtime H",
            "OK",
            "NG",
            "Yield %",
            "Output/H",
        ])

        self.product_table = DashboardTable([
            "Product",
            "OK",
            "NG",
            "Total",
            "Yield %",
            "NG %",
        ])

        self.work_order_table = DashboardTable([
            "Work Order",
            "OK",
            "NG",
            "Total",
            "Yield %",
            "Runtime H",
        ])

        self.ng_table = DashboardTable([
            "Product",
            "NG Qty",
            "NG %",
            "Total Qty",
        ])

        self.status_label = QLabel(
            "Ready"
        )

        self.build_ui()
        self.connect_events()
        self.refresh_dashboard()

    # ==========================================================
    # UI
    # ==========================================================

    def build_ui(self):
        root_layout = QVBoxLayout(self)

        title = QLabel(
            "FACTORY MES DASHBOARD"
        )

        title.setStyleSheet(
            "font-size:22px;"
            "font-weight:bold;"
        )

        filter_layout = QHBoxLayout()

        filter_layout.addWidget(
            QLabel("From")
        )

        filter_layout.addWidget(
            self.start_date
        )

        filter_layout.addWidget(
            QLabel("To")
        )

        filter_layout.addWidget(
            self.end_date
        )

        filter_layout.addWidget(
            self.btn_today
        )

        filter_layout.addWidget(
            self.btn_month
        )

        filter_layout.addStretch()

        filter_layout.addWidget(
            self.btn_refresh
        )

        kpi_layout = QGridLayout()

        cards = [
            self.card_output,
            self.card_ok,
            self.card_ng,
            self.card_yield,
            self.card_runtime,
            self.card_downtime,
            self.card_output_hour,
            self.card_oee,
        ]

        for index, card in enumerate(cards):
            row = index // 4
            column = index % 4

            kpi_layout.addWidget(
                card,
                row,
                column,
            )

        machine_group = self.create_group(
            "Machine Performance",
            self.machine_table,
        )

        employee_group = self.create_group(
            "Employee Performance",
            self.employee_table,
        )

        product_group = self.create_group(
            "Product Quality",
            self.product_table,
        )

        work_order_group = self.create_group(
            "Work Order Output",
            self.work_order_table,
        )

        ng_group = self.create_group(
            "Top NG Products",
            self.ng_table,
        )

        content = QWidget()
        content_layout = QVBoxLayout(content)

        content_layout.addLayout(
            kpi_layout
        )

        first_row = QHBoxLayout()
        first_row.addWidget(
            machine_group,
            1,
        )
        first_row.addWidget(
            employee_group,
            1,
        )

        second_row = QHBoxLayout()
        second_row.addWidget(
            product_group,
            1,
        )
        second_row.addWidget(
            work_order_group,
            1,
        )

        content_layout.addLayout(first_row)
        content_layout.addLayout(second_row)
        content_layout.addWidget(ng_group)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)

        root_layout.addWidget(title)
        root_layout.addLayout(
            filter_layout
        )
        root_layout.addWidget(
            scroll,
            1,
        )
        root_layout.addWidget(
            self.status_label
        )

    @staticmethod
    def create_group(
        title,
        widget,
    ):
        group = QGroupBox(title)

        layout = QVBoxLayout(group)
        layout.addWidget(widget)

        return group

    # ==========================================================
    # Events
    # ==========================================================

    def connect_events(self):
        self.btn_refresh.clicked.connect(
            self.refresh_dashboard
        )

        self.btn_today.clicked.connect(
            self.select_today
        )

        self.btn_month.clicked.connect(
            self.select_this_month
        )

    def select_today(self):
        today = QDate.currentDate()

        self.start_date.setDate(today)
        self.end_date.setDate(today)

        self.refresh_dashboard()

    def select_this_month(self):
        today = date.today()

        self.start_date.setDate(
            QDate(
                today.year,
                today.month,
                1,
            )
        )

        self.end_date.setDate(
            QDate.currentDate()
        )

        self.refresh_dashboard()

    # ==========================================================
    # Refresh
    # ==========================================================

    def refresh_dashboard(self):
        start_date = (
            self.start_date
            .date()
            .toPython()
        )

        end_date = (
            self.end_date
            .date()
            .toPython()
        )

        if end_date < start_date:
            QMessageBox.warning(
                self,
                "Dashboard",
                (
                    "End Date cannot be earlier "
                    "than Start Date."
                ),
            )
            return

        try:
            self.setEnabled(False)

            self.status_label.setText(
                "Loading analytics..."
            )

            analytics = (
                self.analytics_service.build(
                    start_date=start_date,
                    end_date=end_date,
                )
            )

            self.apply_analytics(
                analytics
            )

            self.status_label.setText(
                (
                    f"Loaded: {start_date} "
                    f"to {end_date}"
                )
            )

        except Exception as error:
            self.status_label.setText(
                "Dashboard load failed."
            )

            QMessageBox.warning(
                self,
                "Dashboard Error",
                str(error),
            )

        finally:
            self.setEnabled(True)

    # ==========================================================
    # Analytics mapping
    # ==========================================================

    def apply_analytics(
        self,
        analytics,
    ):
        summary = self._get_section(
            analytics,
            "summary",
            {},
        )

        self.card_output.set_value(
            self._value(
                summary,
                "total_qty",
                0,
            ),
            status="NORMAL",
        )

        self.card_ok.set_value(
            self._value(
                summary,
                "ok_qty",
                0,
            ),
            status="GOOD",
        )

        ng_qty = self._value(
            summary,
            "ng_qty",
            0,
        )

        self.card_ng.set_value(
            ng_qty,
            status=(
                "GOOD"
                if ng_qty == 0
                else "DANGER"
            ),
        )

        yield_percent = self._value(
            summary,
            "yield_percent",
            0.0,
        )

        self.card_yield.set_value(
            yield_percent,
            status=self.percent_status(
                yield_percent,
                good=98,
                warning=95,
            ),
        )

        self.card_runtime.set_value(
            self._value(
                summary,
                "runtime_hour",
                0.0,
            ),
            status="NORMAL",
        )

        downtime_hour = self._value(
            summary,
            "downtime_hour",
            0.0,
        )

        self.card_downtime.set_value(
            downtime_hour,
            status=(
                "GOOD"
                if downtime_hour <= 0
                else "WARNING"
            ),
        )

        self.card_output_hour.set_value(
            self._value(
                summary,
                "output_per_hour",
                0.0,
            ),
            status="NORMAL",
        )

        oee = self._get_section(
            analytics,
            "oee",
            {},
        )

        oee_percent = self._value(
            oee,
            "overall",
            self._value(
                oee,
                "oee_percent",
                0.0,
            ),
        )

        self.card_oee.set_value(
            oee_percent,
            status=self.percent_status(
                oee_percent,
                good=85,
                warning=65,
            ),
        )

        self.load_machine_table(
            self._get_section(
                analytics,
                "machine",
                [],
            )
        )

        self.load_employee_table(
            self._get_section(
                analytics,
                "employee",
                [],
            )
        )

        self.load_product_table(
            self._get_section(
                analytics,
                "product",
                [],
            )
        )

        self.load_work_order_table(
            self._get_section(
                analytics,
                "work_order",
                [],
            )
        )

        ng_section = self._get_section(
            analytics,
            "ng",
            {},
        )

        top_ng = self._get_section(
            ng_section,
            "by_product",
            ng_section
            if isinstance(
                ng_section,
                list,
            )
            else [],
        )

        self.load_ng_table(top_ng)

    # ==========================================================
    # Tables
    # ==========================================================

    def load_machine_table(self, items):
        rows = [
            [
                self._value(
                    item,
                    "machine_code",
                    "",
                ),
                self._value(
                    item,
                    "runtime_hour",
                    0.0,
                ),
                self._value(
                    item,
                    "ok_qty",
                    0,
                ),
                self._value(
                    item,
                    "ng_qty",
                    0,
                ),
                self._value(
                    item,
                    "yield_percent",
                    0.0,
                ),
                self._value(
                    item,
                    "output_per_hour",
                    0.0,
                ),
            ]
            for item in items or []
        ]

        self.machine_table.set_rows(rows)

    def load_employee_table(self, items):
        rows = [
            [
                self._value(
                    item,
                    "employee_code",
                    "",
                ),
                self._value(
                    item,
                    "runtime_hour",
                    0.0,
                ),
                self._value(
                    item,
                    "ok_qty",
                    0,
                ),
                self._value(
                    item,
                    "ng_qty",
                    0,
                ),
                self._value(
                    item,
                    "yield_percent",
                    0.0,
                ),
                self._value(
                    item,
                    "output_per_hour",
                    0.0,
                ),
            ]
            for item in items or []
        ]

        self.employee_table.set_rows(rows)

    def load_product_table(self, items):
        rows = [
            [
                self._value(
                    item,
                    "product_code",
                    "",
                ),
                self._value(
                    item,
                    "ok_qty",
                    0,
                ),
                self._value(
                    item,
                    "ng_qty",
                    0,
                ),
                self._value(
                    item,
                    "total_qty",
                    0,
                ),
                self._value(
                    item,
                    "yield_percent",
                    0.0,
                ),
                self._value(
                    item,
                    "ng_percent",
                    0.0,
                ),
            ]
            for item in items or []
        ]

        self.product_table.set_rows(rows)

    def load_work_order_table(
        self,
        items,
    ):
        rows = [
            [
                self._value(
                    item,
                    "work_order_no",
                    "",
                ),
                self._value(
                    item,
                    "ok_qty",
                    0,
                ),
                self._value(
                    item,
                    "ng_qty",
                    0,
                ),
                self._value(
                    item,
                    "total_qty",
                    0,
                ),
                self._value(
                    item,
                    "yield_percent",
                    0.0,
                ),
                self._value(
                    item,
                    "runtime_hour",
                    0.0,
                ),
            ]
            for item in items or []
        ]

        self.work_order_table.set_rows(rows)

    def load_ng_table(self, items):
        rows = [
            [
                self._value(
                    item,
                    "product_code",
                    "",
                ),
                self._value(
                    item,
                    "ng_qty",
                    0,
                ),
                self._value(
                    item,
                    "ng_percent",
                    0.0,
                ),
                self._value(
                    item,
                    "total_qty",
                    0,
                ),
            ]
            for item in items or []
        ]

        self.ng_table.set_rows(rows)

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _get_section(
        source,
        name,
        default,
    ):
        if source is None:
            return default

        if isinstance(source, dict):
            return source.get(
                name,
                default,
            )

        return getattr(
            source,
            name,
            default,
        )

    @staticmethod
    def _value(
        source,
        name,
        default,
    ):
        if source is None:
            return default

        if isinstance(source, dict):
            value = source.get(
                name,
                default,
            )

        else:
            value = getattr(
                source,
                name,
                default,
            )

        if value is None:
            return default

        return value

    @staticmethod
    def percent_status(
        value,
        good,
        warning,
    ):
        value = float(value or 0)

        if value >= good:
            return "GOOD"

        if value >= warning:
            return "WARNING"

        return "DANGER"