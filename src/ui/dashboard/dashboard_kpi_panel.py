from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
)

from src.ui.dashboard.widgets.kpi_card import (
    KPICard,
)


class DashboardKPIPanel(QGroupBox):
    """
    Panel hiển thị KPI tổng quan.

    Dữ liệu đầu vào là kết quả từ
    ManufacturingAnalyticsService.
    """

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(
            "Manufacturing Summary",
            parent,
        )

        self.production_card = KPICard(
            title="Total Production",
            unit="PCS",
            subtitle="OK + NG",
        )

        self.ok_card = KPICard(
            title="OK Quantity",
            unit="PCS",
            subtitle="Accepted quantity",
        )

        self.ng_card = KPICard(
            title="NG Quantity",
            unit="PCS",
            subtitle="Defect quantity",
        )

        self.yield_card = KPICard(
            title="Yield",
            unit="%",
            subtitle="OK / Total",
        )

        self.oee_card = KPICard(
            title="OEE",
            unit="%",
            subtitle="A × P × Q",
        )

        self.runtime_card = KPICard(
            title="Runtime",
            unit="Hour",
            subtitle="Recorded runtime",
        )

        self.downtime_card = KPICard(
            title="Downtime",
            unit="Hour",
            subtitle="Production downtime",
        )

        self.utilization_card = KPICard(
            title="Utilization",
            unit="%",
            subtitle="Machine utilization",
        )

        self._cards = [
            self.production_card,
            self.ok_card,
            self.ng_card,
            self.yield_card,
            self.oee_card,
            self.runtime_card,
            self.downtime_card,
            self.utilization_card,
        ]

        self._build_ui()

    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):
        layout = QGridLayout(self)

        layout.setContentsMargins(
            10,
            12,
            10,
            10,
        )

        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(10)

        for index, card in enumerate(
            self._cards
        ):
            row = index // 4
            column = index % 4

            layout.addWidget(
                card,
                row,
                column,
            )

            layout.setColumnStretch(
                column,
                1,
            )

    # ==========================================================
    # Update
    # ==========================================================

    def update_data(
        self,
        analytics,
    ):
        summary = self._section(
            analytics,
            "summary",
            {},
        )

        oee = self._section(
            analytics,
            "oee",
            {},
        )

        total_qty = self._number(
            self._value(
                summary,
                "total_qty",
                0,
            )
        )

        ok_qty = self._number(
            self._value(
                summary,
                "ok_qty",
                0,
            )
        )

        ng_qty = self._number(
            self._value(
                summary,
                "ng_qty",
                0,
            )
        )

        yield_percent = self._number(
            self._value(
                summary,
                "yield_percent",
                0,
            )
        )

        runtime_hour = self._number(
            self._value(
                summary,
                "runtime_hour",
                0,
            )
        )

        downtime_hour = self._number(
            self._value(
                summary,
                "downtime_hour",
                0,
            )
        )

        utilization_percent = self._number(
            self._value(
                summary,
                "utilization_percent",
                self._value(
                    summary,
                    "availability_percent",
                    0,
                ),
            )
        )

        oee_percent = self._number(
            self._value(
                oee,
                "overall",
                self._value(
                    oee,
                    "oee_percent",
                    0,
                ),
            )
        )

        self.production_card.set_value(
            total_qty,
            status="INFO",
        )

        self.ok_card.set_value(
            ok_qty,
            status="GOOD",
        )

        self.ng_card.set_value(
            ng_qty,
            status=(
                "GOOD"
                if ng_qty <= 0
                else "DANGER"
            ),
        )

        self.yield_card.set_value(
            yield_percent,
            status=self._higher_is_better(
                yield_percent,
                good=98.0,
                warning=95.0,
            ),
        )

        self.oee_card.set_value(
            oee_percent,
            status=self._higher_is_better(
                oee_percent,
                good=85.0,
                warning=65.0,
            ),
        )

        self.runtime_card.set_value(
            runtime_hour,
            status="INFO",
        )

        self.downtime_card.set_value(
            downtime_hour,
            status=self._lower_is_better(
                downtime_hour,
                good=0.5,
                warning=2.0,
            ),
        )

        self.utilization_card.set_value(
            utilization_percent,
            status=self._higher_is_better(
                utilization_percent,
                good=85.0,
                warning=65.0,
            ),
        )

    def clear_data(self):
        for card in self._cards:
            card.clear_value()

    # ==========================================================
    # Status helpers
    # ==========================================================

    @staticmethod
    def _higher_is_better(
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

    @staticmethod
    def _lower_is_better(
        value,
        good,
        warning,
    ):
        value = float(value or 0)

        if value <= good:
            return "GOOD"

        if value <= warning:
            return "WARNING"

        return "DANGER"

    # ==========================================================
    # Data helpers
    # ==========================================================

    @staticmethod
    def _section(
        source,
        field_name,
        default,
    ):
        if source is None:
            return default

        if isinstance(source, dict):
            return source.get(
                field_name,
                default,
            )

        return getattr(
            source,
            field_name,
            default,
        )

    @staticmethod
    def _value(
        source,
        field_name,
        default,
    ):
        if source is None:
            return default

        if isinstance(source, dict):
            value = source.get(
                field_name,
                default,
            )

        else:
            value = getattr(
                source,
                field_name,
                default,
            )

        return (
            default
            if value is None
            else value
        )

    @staticmethod
    def _number(value):
        try:
            return float(value or 0)

        except (
            TypeError,
            ValueError,
        ):
            return 0.0