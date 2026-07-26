from __future__ import annotations

from math import isfinite
from typing import Iterable, Sequence

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QChart,
    QChartView,
    QLineSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.services.trend_service import (
    TrendGranularity,
    TrendPoint,
)


class TrendWidget(QWidget):
    """
    Biểu đồ xu hướng OEE.

    Hiển thị bốn chỉ số:
    - OEE
    - Availability
    - Performance
    - Quality

    Widget chỉ chịu trách nhiệm hiển thị TrendPoint.
    Việc tổng hợp dữ liệu thuộc TrendService.
    """

    granularity_changed = Signal(object)

    SERIES_FIELDS = (
        ("OEE", "oee"),
        ("Availability", "availability"),
        ("Performance", "performance"),
        ("Quality", "quality"),
    )

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._data: tuple[TrendPoint, ...] = ()
        self._series: dict[str, QLineSeries] = {}

        self._build_ui()
        self._build_chart()
        self._connect_signals()
        self.clear()

    @property
    def data(self) -> tuple[TrendPoint, ...]:
        return self._data

    @property
    def granularity(self) -> TrendGranularity:
        raw_value = self.granularity_combo.currentData()

        try:
            return TrendGranularity(raw_value)
        except (TypeError, ValueError):
            return TrendGranularity.DAILY

    @property
    def series(self) -> dict[str, QLineSeries]:
        return dict(self._series)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        control_layout = QHBoxLayout()

        title_label = QLabel("OEE Trend")
        title_label.setObjectName("trendTitle")

        granularity_label = QLabel("Chu kỳ:")

        self.granularity_combo = QComboBox()
        self.granularity_combo.addItem(
            "Theo giờ",
            TrendGranularity.HOURLY,
        )
        self.granularity_combo.addItem(
            "Theo ngày",
            TrendGranularity.DAILY,
        )
        self.granularity_combo.addItem(
            "Theo tuần",
            TrendGranularity.WEEKLY,
        )
        self.granularity_combo.addItem(
            "Theo tháng",
            TrendGranularity.MONTHLY,
        )
        self.granularity_combo.addItem(
            "Theo năm",
            TrendGranularity.YEARLY,
        )

        daily_index = self.granularity_combo.findData(
            TrendGranularity.DAILY
        )

        if daily_index >= 0:
            self.granularity_combo.setCurrentIndex(
                daily_index
            )

        control_layout.addWidget(title_label)
        control_layout.addStretch()
        control_layout.addWidget(granularity_label)
        control_layout.addWidget(
            self.granularity_combo
        )

        root.addLayout(control_layout)

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )
        self.chart_view.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.chart_view.setMinimumHeight(340)

        root.addWidget(self.chart_view, 1)

        self.empty_label = QLabel(
            "Không có dữ liệu xu hướng."
        )
        self.empty_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.empty_label.setObjectName(
            "trendEmptyLabel"
        )

        root.addWidget(self.empty_label)

        self.setStyleSheet(
            """
            QLabel#trendTitle {
                font-size: 16px;
                font-weight: 700;
            }

            QLabel#trendEmptyLabel {
                padding: 18px;
            }

            QComboBox {
                min-height: 28px;
                min-width: 120px;
            }
            """
        )

    def _build_chart(self) -> None:
        self.chart = QChart()
        self.chart.setTitle(
            "OEE / Availability / Performance / Quality"
        )
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(
            Qt.AlignmentFlag.AlignBottom
        )

        self.category_axis = QBarCategoryAxis()
        self.value_axis = QValueAxis()

        self.value_axis.setRange(0.0, 100.0)
        self.value_axis.setLabelFormat("%.1f")
        self.value_axis.setTitleText("Tỷ lệ (%)")
        self.value_axis.setTickCount(6)

        self.chart.addAxis(
            self.category_axis,
            Qt.AlignmentFlag.AlignBottom,
        )
        self.chart.addAxis(
            self.value_axis,
            Qt.AlignmentFlag.AlignLeft,
        )

        for display_name, field_name in self.SERIES_FIELDS:
            series = QLineSeries()
            series.setName(display_name)
            series.setPointsVisible(True)

            self.chart.addSeries(series)

            series.attachAxis(self.category_axis)
            series.attachAxis(self.value_axis)

            self._series[field_name] = series

        self.chart_view.setChart(self.chart)

    def _connect_signals(self) -> None:
        self.granularity_combo.currentIndexChanged.connect(
            self._emit_granularity_changed
        )

    def _emit_granularity_changed(
        self,
        index: int,
    ) -> None:
        del index

        self.granularity_changed.emit(
            self.granularity
        )

    def set_data(
        self,
        points: Iterable[TrendPoint] | None,
    ) -> None:
        normalized = tuple(points or ())
        self._data = normalized

        self._clear_series()
        self.category_axis.clear()

        if not normalized:
            self._update_empty_state(True)
            return

        categories: list[str] = []

        for index, point in enumerate(normalized):
            categories.append(point.label)

            for _, field_name in self.SERIES_FIELDS:
                series = self._series[field_name]
                value = self._percentage_value(
                    getattr(point, field_name, 0)
                )

                series.append(
                    float(index),
                    value,
                )

        self.category_axis.append(categories)
        self._update_empty_state(False)

    def clear(self) -> None:
        self._data = ()
        self._clear_series()
        self.category_axis.clear()
        self._update_empty_state(True)

    def set_granularity(
        self,
        granularity: TrendGranularity | str,
    ) -> None:
        try:
            resolved = TrendGranularity(granularity)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Granularity không hợp lệ."
            ) from exc

        index = self.granularity_combo.findData(
            resolved
        )

        if index < 0:
            raise ValueError(
                f"Không tìm thấy granularity: {resolved}"
            )

        self.granularity_combo.setCurrentIndex(index)

    def _clear_series(self) -> None:
        for series in self._series.values():
            series.clear()

    def _update_empty_state(
        self,
        empty: bool,
    ) -> None:
        self.empty_label.setVisible(empty)
        self.chart_view.setVisible(not empty)

    @staticmethod
    def _percentage_value(
        value: int | float,
    ) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            return 0.0

        if not isfinite(number):
            return 0.0

        # Hỗ trợ cả dữ liệu dạng 0–1 và 0–100.
        if 0.0 <= number <= 1.0:
            return round(number * 100.0, 4)

        return round(number, 4)
