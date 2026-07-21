from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from src.ui.charts.chart_formatter import (
    ChartFormatter,
)
from src.ui.charts.chart_theme import (
    ChartTheme,
)


class KPICard(QFrame):
    """
    KPI Card dùng chung cho Dashboard.

    Hỗ trợ:
    - Title
    - Value
    - Unit
    - Subtitle
    - Trend
    - Status color
    - ChartFormatter
    """

    VALID_STATUSES = {
        "GOOD",
        "WARNING",
        "DANGER",
        "INFO",
        "NORMAL",
    }

    def __init__(
        self,
        title,
        unit="",
        subtitle="",
        parent=None,
    ):
        super().__init__(parent)

        self._title = str(title or "")
        self._unit = str(unit or "")
        self._subtitle = str(subtitle or "")

        self._raw_value = 0
        self._status = "NORMAL"
        self._trend_value = None

        self.setObjectName(
            "DashboardKPICard"
        )

        self.setMinimumWidth(155)
        self.setMinimumHeight(125)

        self.title_label = QLabel(
            self._title
        )

        self.value_label = QLabel("0")

        self.unit_label = QLabel(
            self._unit
        )

        self.subtitle_label = QLabel(
            self._subtitle
        )

        self.trend_label = QLabel("")

        self._build_ui()
        self._apply_style()

    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):
        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(
            14,
            11,
            14,
            11,
        )

        root_layout.setSpacing(4)

        header_layout = QHBoxLayout()

        self.title_label.setStyleSheet(
            "font-size:13px;"
            "font-weight:600;"
            "color:#546E7A;"
        )

        self.trend_label.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )

        self.trend_label.setStyleSheet(
            "font-size:11px;"
            "font-weight:bold;"
        )

        header_layout.addWidget(
            self.title_label
        )

        header_layout.addStretch()

        header_layout.addWidget(
            self.trend_label
        )

        value_layout = QHBoxLayout()

        value_layout.setSpacing(5)

        self.value_label.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter
        )

        self.unit_label.setAlignment(
            Qt.AlignLeft | Qt.AlignBottom
        )

        self.unit_label.setStyleSheet(
            "font-size:11px;"
            "color:#78909C;"
            "padding-bottom:4px;"
        )

        value_layout.addWidget(
            self.value_label
        )

        value_layout.addWidget(
            self.unit_label
        )

        value_layout.addStretch()

        self.subtitle_label.setStyleSheet(
            "font-size:11px;"
            "color:#90A4AE;"
        )

        self.subtitle_label.setWordWrap(True)

        root_layout.addLayout(
            header_layout
        )

        root_layout.addStretch()

        root_layout.addLayout(
            value_layout
        )

        root_layout.addWidget(
            self.subtitle_label
        )

    # ==========================================================
    # Public API
    # ==========================================================

    def set_value(
        self,
        value,
        unit=None,
        status=None,
        decimals=None,
    ):
        self._raw_value = value

        if unit is not None:
            self._unit = str(unit or "")
            self.unit_label.setText(
                self._unit
            )

        formatted_value = (
            self._format_value(
                value=value,
                unit=self._unit,
                decimals=decimals,
            )
        )

        self.value_label.setText(
            formatted_value
        )

        if status is not None:
            self.set_status(status)

    def set_status(
        self,
        status,
    ):
        normalized = str(
            status or "NORMAL"
        ).strip().upper()

        if normalized not in self.VALID_STATUSES:
            normalized = "NORMAL"

        self._status = normalized

        self._apply_style()

    def set_trend(
        self,
        value,
        suffix="%",
    ):
        if value is None:
            self._trend_value = None
            self.trend_label.clear()
            return

        try:
            trend = float(value)

        except (
            TypeError,
            ValueError,
        ):
            self._trend_value = None
            self.trend_label.clear()
            return

        self._trend_value = trend

        if trend > 0:
            prefix = "▲"
            color = ChartTheme.GOOD

        elif trend < 0:
            prefix = "▼"
            color = ChartTheme.DANGER

        else:
            prefix = "●"
            color = ChartTheme.NORMAL

        self.trend_label.setText(
            f"{prefix} {abs(trend):.1f}{suffix}"
        )

        self.trend_label.setStyleSheet(
            f"font-size:11px;"
            f"font-weight:bold;"
            f"color:{color};"
        )

    def set_title(
        self,
        title,
    ):
        self._title = str(title or "")

        self.title_label.setText(
            self._title
        )

    def set_subtitle(
        self,
        subtitle,
    ):
        self._subtitle = str(
            subtitle or ""
        )

        self.subtitle_label.setText(
            self._subtitle
        )

    def clear_value(self):
        self._raw_value = 0
        self.value_label.setText("-")
        self.trend_label.clear()
        self.set_status("NORMAL")

    # ==========================================================
    # Formatter
    # ==========================================================

    @staticmethod
    def _format_value(
        value,
        unit,
        decimals=None,
    ):
        normalized_unit = str(
            unit or ""
        ).strip().lower()

        if normalized_unit in {
            "pcs",
            "qty",
        }:
            return (
                ChartFormatter
                .format_integer(value)
            )

        if normalized_unit in {
            "%",
            "percent",
        }:
            decimal_count = (
                2
                if decimals is None
                else int(decimals)
            )

            number = (
                ChartFormatter.to_float(value)
            )

            return (
                ChartFormatter.format_number(
                    number,
                    decimal_count,
                )
            )

        if normalized_unit in {
            "hour",
            "hours",
            "h",
        }:
            number = (
                ChartFormatter.to_float(value)
            )

            return f"{number:,.2f}"

        if normalized_unit in {
            "minute",
            "minutes",
            "min",
        }:
            number = (
                ChartFormatter.to_float(value)
            )

            return f"{number:,.1f}"

        if normalized_unit in {
            "second",
            "seconds",
            "sec",
            "s",
        }:
            return (
                ChartFormatter
                .format_integer(value)
            )

        if decimals is None:
            decimals = 2

        return (
            ChartFormatter.format_number(
                value,
                decimals,
            )
        )

    # ==========================================================
    # Style
    # ==========================================================

    def _apply_style(self):
        status_color = (
            ChartTheme.status_color(
                self._status
            )
        )

        self.setStyleSheet(f"""
            QFrame#DashboardKPICard {{
                background: {ChartTheme.CARD_BACKGROUND};
                border: 1px solid {ChartTheme.BORDER_COLOR};
                border-left: 5px solid {status_color};
                border-radius: 8px;
            }}
        """)

        self.value_label.setStyleSheet(
            f"font-size:27px;"
            f"font-weight:bold;"
            f"color:{status_color};"
        )