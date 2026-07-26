from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from math import isfinite
from typing import Any, Iterable, Mapping

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True, slots=True)
class TrendPoint:
    """
    Một điểm dữ liệu đã được chuẩn hóa để hiển thị trên biểu đồ xu hướng.
    """

    label: str
    oee: float = 0.0
    availability: float = 0.0
    performance: float = 0.0
    quality: float = 0.0


class _TrendCanvas(QWidget):
    """
    Canvas nội bộ chịu trách nhiệm vẽ biểu đồ.

    Không chứa logic nghiệp vụ và không truy cập service/repository.
    """

    SERIES = (
        ("oee", QColor(25, 118, 210)),
        ("availability", QColor(46, 125, 50)),
        ("performance", QColor(245, 124, 0)),
        ("quality", QColor(123, 31, 162)),
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._points: tuple[TrendPoint, ...] = ()
        self._visible_series = {
            series: True
            for series, _ in self.SERIES
        }

        self.setMinimumHeight(250)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def set_points(
        self,
        points: Iterable[TrendPoint],
    ) -> None:
        self._points = tuple(points)
        self.update()

    def set_series_visible(
        self,
        series: str,
        visible: bool,
    ) -> None:
        if series not in self._visible_series:
            raise KeyError(
                f"Unknown trend series: {series}"
            )

        self._visible_series[series] = bool(visible)
        self.update()

    def is_series_visible(
        self,
        series: str,
    ) -> bool:
        if series not in self._visible_series:
            raise KeyError(
                f"Unknown trend series: {series}"
            )

        return self._visible_series[series]

    def paintEvent(self, event) -> None:  # noqa: N802
        del event

        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        painter.fillRect(
            self.rect(),
            self.palette().base(),
        )

        plot_rect = QRectF(
            52.0,
            14.0,
            max(1.0, self.width() - 72.0),
            max(1.0, self.height() - 56.0),
        )

        self._draw_grid(
            painter,
            plot_rect,
        )

        if not self._points:
            self._draw_empty_state(
                painter,
                plot_rect,
            )
            return

        for series, color in self.SERIES:
            if self._visible_series[series]:
                self._draw_series(
                    painter,
                    plot_rect,
                    series,
                    color,
                )

        self._draw_x_labels(
            painter,
            plot_rect,
        )

    def _draw_grid(
        self,
        painter: QPainter,
        plot_rect: QRectF,
    ) -> None:
        font = QFont(self.font())
        font.setPointSizeF(
            max(
                8.0,
                font.pointSizeF() - 1.0,
            )
        )
        painter.setFont(font)

        grid_pen = QPen(
            QColor(215, 220, 228),
            1.0,
        )

        for value in range(0, 101, 20):
            y = (
                plot_rect.bottom()
                - (value / 100.0)
                * plot_rect.height()
            )

            painter.setPen(grid_pen)
            painter.drawLine(
                QPointF(
                    plot_rect.left(),
                    y,
                ),
                QPointF(
                    plot_rect.right(),
                    y,
                ),
            )

            painter.setPen(
                self.palette().text().color()
            )
            painter.drawText(
                QRectF(
                    2.0,
                    y - 9.0,
                    44.0,
                    18.0,
                ),
                (
                    Qt.AlignmentFlag.AlignRight
                    | Qt.AlignmentFlag.AlignVCenter
                ),
                str(value),
            )

        painter.setPen(
            QPen(
                QColor(145, 150, 160),
                1.0,
            )
        )
        painter.drawRect(plot_rect)

    def _draw_empty_state(
        self,
        painter: QPainter,
        plot_rect: QRectF,
    ) -> None:
        painter.setPen(
            self.palette().text().color()
        )

        painter.drawText(
            plot_rect,
            Qt.AlignmentFlag.AlignCenter,
            "No trend data",
        )

    def _draw_series(
        self,
        painter: QPainter,
        plot_rect: QRectF,
        series: str,
        color: QColor,
    ) -> None:
        path = QPainterPath()
        coordinates: list[QPointF] = []

        for index, point in enumerate(
            self._points
        ):
            x = self._x_for_index(
                plot_rect,
                index,
            )

            value = float(
                getattr(
                    point,
                    series,
                )
            )

            y = (
                plot_rect.bottom()
                - (value / 100.0)
                * plot_rect.height()
            )

            coordinate = QPointF(x, y)
            coordinates.append(coordinate)

            if index == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        painter.setPen(
            QPen(
                color,
                2.2,
            )
        )
        painter.drawPath(path)

        painter.setBrush(color)

        for coordinate in coordinates:
            painter.drawEllipse(
                coordinate,
                3.0,
                3.0,
            )

    def _draw_x_labels(
        self,
        painter: QPainter,
        plot_rect: QRectF,
    ) -> None:
        count = len(self._points)

        if count == 0:
            return

        max_labels = 8
        step = max(
            1,
            count // max_labels,
        )

        indexes = list(
            range(
                0,
                count,
                step,
            )
        )

        last_index = count - 1

        if indexes[-1] != last_index:
            indexes.append(last_index)

        painter.setPen(
            self.palette().text().color()
        )

        for index in indexes:
            x = self._x_for_index(
                plot_rect,
                index,
            )

            painter.drawText(
                QRectF(
                    x - 36.0,
                    plot_rect.bottom() + 7.0,
                    72.0,
                    22.0,
                ),
                (
                    Qt.AlignmentFlag.AlignHCenter
                    | Qt.AlignmentFlag.AlignTop
                ),
                self._points[index].label,
            )

    def _x_for_index(
        self,
        plot_rect: QRectF,
        index: int,
    ) -> float:
        if len(self._points) <= 1:
            return plot_rect.center().x()

        ratio = index / (
            len(self._points) - 1
        )

        return (
            plot_rect.left()
            + ratio * plot_rect.width()
        )


class OEETrendWidget(QWidget):
    """
    Widget hiển thị xu hướng:

    - OEE
    - Availability
    - Performance
    - Quality

    Widget chỉ chịu trách nhiệm trình bày dữ liệu.

    Public API:
        set_data(rows)
        clear()
        data()
        point_count()
        set_series_visible(series, visible)
        is_series_visible(series)
    """

    SERIES_KEYS = (
        "oee",
        "availability",
        "performance",
        "quality",
    )

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._points: tuple[
            TrendPoint,
            ...
        ] = ()

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )
        root_layout.setSpacing(8)

        self.title_label = QLabel(
            "OEE Trend"
        )

        title_font = self.title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(
            title_font.pointSize() + 2
        )
        self.title_label.setFont(
            title_font
        )

        root_layout.addWidget(
            self.title_label
        )

        toggle_layout = QHBoxLayout()

        labels = {
            "oee": "OEE",
            "availability": "Availability",
            "performance": "Performance",
            "quality": "Quality",
        }

        self._checkboxes: dict[
            str,
            QCheckBox,
        ] = {}

        for series in self.SERIES_KEYS:
            checkbox = QCheckBox(
                labels[series]
            )
            checkbox.setChecked(True)

            self._checkboxes[
                series
            ] = checkbox

            toggle_layout.addWidget(
                checkbox
            )

        toggle_layout.addStretch(1)

        root_layout.addLayout(
            toggle_layout
        )

        self.canvas = _TrendCanvas(self)

        root_layout.addWidget(
            self.canvas,
            1,
        )

    def _connect_signals(self) -> None:
        for series, checkbox in (
            self._checkboxes.items()
        ):
            checkbox.toggled.connect(
                lambda checked, key=series:
                self.canvas.set_series_visible(
                    key,
                    checked,
                )
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_title(
        self,
        title: str,
    ) -> None:
        self.title_label.setText(
            str(title)
        )

    def title(self) -> str:
        return self.title_label.text()

    def set_data(
        self,
        rows: Iterable[Any] | None,
    ) -> None:
        self._points = tuple(
            self._convert_row(row)
            for row in (rows or ())
        )

        self.canvas.set_points(
            self._points
        )

    def clear(self) -> None:
        self.set_data(())

    def data(
        self,
    ) -> tuple[TrendPoint, ...]:
        return self._points

    def point_count(self) -> int:
        return len(self._points)

    def set_series_visible(
        self,
        series: str,
        visible: bool,
    ) -> None:
        normalized = (
            str(series)
            .strip()
            .lower()
        )

        if normalized not in self._checkboxes:
            raise KeyError(
                f"Unknown trend series: {series}"
            )

        self._checkboxes[
            normalized
        ].setChecked(
            bool(visible)
        )

    def is_series_visible(
        self,
        series: str,
    ) -> bool:
        normalized = (
            str(series)
            .strip()
            .lower()
        )

        if normalized not in self._checkboxes:
            raise KeyError(
                f"Unknown trend series: {series}"
            )

        return self._checkboxes[
            normalized
        ].isChecked()

    # ------------------------------------------------------------------
    # Data conversion
    # ------------------------------------------------------------------

    @classmethod
    def _convert_row(
        cls,
        row: Any,
    ) -> TrendPoint:
        if isinstance(
            row,
            TrendPoint,
        ):
            return row

        if isinstance(
            row,
            Mapping,
        ):
            getter = row.get
        else:

            def getter(
                name: str,
                default: Any = None,
            ) -> Any:
                return getattr(
                    row,
                    name,
                    default,
                )

        label_value = getter("label")

        if label_value is None:
            label_value = getter(
                "report_date"
            )

        if label_value is None:
            label_value = getter("date")

        return TrendPoint(
            label=cls._format_label(
                label_value
            ),
            oee=cls._to_percentage(
                getter("oee")
            ),
            availability=cls._to_percentage(
                getter("availability")
            ),
            performance=cls._to_percentage(
                getter("performance")
            ),
            quality=cls._to_percentage(
                getter("quality")
            ),
        )

    @staticmethod
    def _format_label(
        value: Any,
    ) -> str:
        if value is None:
            return ""

        if isinstance(
            value,
            (date, datetime),
        ):
            return value.strftime(
                "%d/%m"
            )

        return str(value).strip()

    @staticmethod
    def _to_percentage(
        value: Any,
    ) -> float:
        if value is None:
            return 0.0

        if isinstance(value, str):
            value = (
                value.strip()
                .replace(",", "")
                .replace("%", "")
            )

            if not value:
                return 0.0

        try:
            number = float(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

        if not isfinite(number):
            return 0.0

        return max(
            0.0,
            min(
                100.0,
                number,
            ),
        )