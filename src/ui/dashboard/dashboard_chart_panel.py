from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.ui.charts.line_chart import (
    LineChart,
)
from src.ui.charts.ranking_chart import (
    RankingChart,
)


class DashboardChartPanel(QGroupBox):
    """
    Panel biểu đồ cho Dashboard.

    Dữ liệu đầu vào là kết quả từ:
        DashboardChartService.build()

    Panel không tự tính Analytics.
    """

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(
            "Manufacturing Analytics",
            parent,
        )

        self.daily_output_chart = LineChart(
            title="Daily Output Trend",
            subtitle="Daily total, OK and NG quantity",
        )

        self.oee_trend_chart = LineChart(
            title="Daily OEE Trend",
            subtitle=(
                "Availability, Performance, "
                "Quality and OEE"
            ),
        )

        self.machine_ranking_chart = (
            RankingChart(
                title="Machine Output Ranking",
                subtitle="Top machines by OK quantity",
                top_n=10,
            )
        )

        self.employee_ranking_chart = (
            RankingChart(
                title="Employee Output Ranking",
                subtitle="Top employees by OK quantity",
                top_n=10,
            )
        )

        self.ng_pareto_placeholder = (
            self._create_placeholder(
                title="NG Pareto",
                message=(
                    "ParetoChart will be added "
                    "in the next commit."
                ),
            )
        )

        self._charts = [
            self.daily_output_chart,
            self.oee_trend_chart,
            self.machine_ranking_chart,
            self.employee_ranking_chart,
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

        layout.addWidget(
            self.daily_output_chart,
            0,
            0,
        )

        layout.addWidget(
            self.oee_trend_chart,
            0,
            1,
        )

        layout.addWidget(
            self.machine_ranking_chart,
            1,
            0,
        )

        layout.addWidget(
            self.employee_ranking_chart,
            1,
            1,
        )

        layout.addWidget(
            self.ng_pareto_placeholder,
            2,
            0,
            1,
            2,
        )

        layout.setColumnStretch(
            0,
            1,
        )

        layout.setColumnStretch(
            1,
            1,
        )

    @staticmethod
    def _create_placeholder(
        title,
        message,
    ):
        widget = QWidget()

        widget.setMinimumHeight(300)

        layout = QVBoxLayout(widget)

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            "font-size:16px;"
            "font-weight:bold;"
        )

        message_label = QLabel(
            message
        )

        message_label.setStyleSheet(
            "font-size:13px;"
            "color:#78909C;"
        )

        layout.addWidget(
            title_label
        )

        layout.addStretch()

        layout.addWidget(
            message_label
        )

        layout.addStretch()

        widget.setStyleSheet("""
            QWidget {
                background: #FFFFFF;
                border: 1px solid #CFD8DC;
                border-radius: 8px;
            }
        """)

        return widget

    # ==========================================================
    # Update
    # ==========================================================

    def update_data(
        self,
        chart_data,
    ):
        chart_data = chart_data or {}

        self.daily_output_chart.load_data(
            self._section(
                chart_data,
                "daily_output",
                None,
            )
        )

        self.oee_trend_chart.load_data(
            self._section(
                chart_data,
                "oee_trend",
                None,
            )
        )

        self.machine_ranking_chart.load_data(
            self._section(
                chart_data,
                "machine_ranking",
                None,
            )
        )

        self.employee_ranking_chart.load_data(
            self._section(
                chart_data,
                "employee_ranking",
                None,
            )
        )

    def clear_data(self):
        for chart in self._charts:
            chart.clear_chart()

    def set_loading(
        self,
        loading,
    ):
        for chart in self._charts:
            chart.setEnabled(
                not loading
            )

    # ==========================================================
    # Helpers
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