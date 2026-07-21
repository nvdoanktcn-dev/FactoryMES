from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QSizePolicy, QWidget


@dataclass(slots=True, frozen=True)
class OEETrendPoint:
    """
    Một điểm dữ liệu OEE theo thời gian.

    label:
        Nhãn hiển thị trên trục X, ví dụ 01/07 hoặc 2026-07.

    oee, availability, performance, quality:
        Giá trị phần trăm từ 0 đến 100.
    """

    label: str
    oee: float
    availability: float = 0.0
    performance: float = 0.0
    quality: float = 0.0


class OEETrendChart(QWidget):
    """
    Biểu đồ xu hướng OEE thuần PySide6/QPainter.

    Không phụ thuộc matplotlib hoặc QtCharts.

    Series hỗ trợ:
    - OEE
    - Availability
    - Performance
    - Quality
    """

    SERIES = (
        ("oee", "OEE", QColor("#1565C0")),
        (
            "availability",
            "Availability",
            QColor("#2E7D32"),
        ),
        (
            "performance",
            "Performance",
            QColor("#EF6C00"),
        ),
        (
            "quality",
            "Quality",
            QColor("#6A1B9A"),
        ),
    )

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._points: list[OEETrendPoint] = []
        self._visible_series = {
            "oee": True,
            "availability": True,
            "performance": True,
            "quality": True,
        }

        self.setMinimumHeight(280)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.setMouseTracking(True)

    def set_points(
        self,
        points: Iterable[OEETrendPoint],
    ) -> None:
        self._points = list(points)
        self.update()

    def clear(self) -> None:
        self._points.clear()
        self.update()

    def set_series_visible(
        self,
        series_name: str,
        visible: bool,
    ) -> None:
        if series_name not in self._visible_series:
            raise KeyError(
                f"Unknown OEE series: {series_name}"
            )

        self._visible_series[series_name] = bool(
            visible
        )
        self.update()

    def is_series_visible(
        self,
        series_name: str,
    ) -> bool:
        return bool(
            self._visible_series.get(
                series_name,
                False,
            )
        )

    def paintEvent(self, event) -> None:
        del event

        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        self._draw_background(painter)

        if not self._points:
            self._draw_empty_state(painter)
            return

        chart_rect = self._chart_rect()

        self._draw_grid(
            painter,
            chart_rect,
        )
        self._draw_axes(
            painter,
            chart_rect,
        )
        self._draw_x_labels(
            painter,
            chart_rect,
        )

        for (
            field_name,
            label,
            color,
        ) in self.SERIES:
            if not self._visible_series.get(
                field_name,
                False,
            ):
                continue

            self._draw_series(
                painter=painter,
                chart_rect=chart_rect,
                field_name=field_name,
                color=color,
            )

        self._draw_legend(
            painter
        )

    def _draw_background(
        self,
        painter: QPainter,
    ) -> None:
        painter.fillRect(
            self.rect(),
            QColor("#FFFFFF"),
        )

    def _draw_empty_state(
        self,
        painter: QPainter,
    ) -> None:
        painter.setPen(
            QColor("#607D8B")
        )
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "Không có dữ liệu OEE trong khoảng đã chọn.",
        )

    def _chart_rect(self) -> QRectF:
        left = 58.0
        top = 42.0
        right = 24.0
        bottom = 48.0

        return QRectF(
            left,
            top,
            max(
                10.0,
                self.width() - left - right,
            ),
            max(
                10.0,
                self.height() - top - bottom,
            ),
        )

    def _draw_grid(
        self,
        painter: QPainter,
        chart_rect: QRectF,
    ) -> None:
        grid_pen = QPen(
            QColor("#E0E0E0")
        )
        grid_pen.setWidthF(1.0)
        painter.setPen(grid_pen)

        for value in range(
            0,
            101,
            20,
        ):
            y = self._value_to_y(
                value,
                chart_rect,
            )

            painter.drawLine(
                QPointF(
                    chart_rect.left(),
                    y,
                ),
                QPointF(
                    chart_rect.right(),
                    y,
                ),
            )

            painter.setPen(
                QColor("#546E7A")
            )
            painter.drawText(
                QRectF(
                    4.0,
                    y - 10.0,
                    48.0,
                    20.0,
                ),
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter,
                f"{value}%",
            )
            painter.setPen(grid_pen)

    def _draw_axes(
        self,
        painter: QPainter,
        chart_rect: QRectF,
    ) -> None:
        axis_pen = QPen(
            QColor("#78909C")
        )
        axis_pen.setWidthF(1.2)
        painter.setPen(axis_pen)

        painter.drawLine(
            chart_rect.bottomLeft(),
            chart_rect.bottomRight(),
        )
        painter.drawLine(
            chart_rect.topLeft(),
            chart_rect.bottomLeft(),
        )

    def _draw_x_labels(
        self,
        painter: QPainter,
        chart_rect: QRectF,
    ) -> None:
        count = len(self._points)

        if count == 0:
            return

        font_metrics = QFontMetrics(
            painter.font()
        )

        max_labels = max(
            2,
            int(
                chart_rect.width() // 90
            ),
        )
        step = max(
            1,
            (count + max_labels - 1)
            // max_labels,
        )

        painter.setPen(
            QColor("#546E7A")
        )

        for index, point in enumerate(
            self._points
        ):
            if (
                index % step != 0
                and index != count - 1
            ):
                continue

            x = self._index_to_x(
                index,
                count,
                chart_rect,
            )
            label = str(
                point.label
            )
            width = max(
                60,
                font_metrics.horizontalAdvance(
                    label
                )
                + 8,
            )

            painter.drawText(
                QRectF(
                    x - width / 2,
                    chart_rect.bottom() + 8,
                    width,
                    24,
                ),
                Qt.AlignmentFlag.AlignHCenter
                | Qt.AlignmentFlag.AlignTop,
                label,
            )

    def _draw_series(
        self,
        *,
        painter: QPainter,
        chart_rect: QRectF,
        field_name: str,
        color: QColor,
    ) -> None:
        count = len(self._points)

        if count == 0:
            return

        path = QPainterPath()

        for index, point in enumerate(
            self._points
        ):
            value = self._clamp_percentage(
                getattr(
                    point,
                    field_name,
                    0.0,
                )
            )
            x = self._index_to_x(
                index,
                count,
                chart_rect,
            )
            y = self._value_to_y(
                value,
                chart_rect,
            )

            if index == 0:
                path.moveTo(
                    x,
                    y,
                )
            else:
                path.lineTo(
                    x,
                    y,
                )

        pen = QPen(color)
        pen.setWidthF(2.2)
        painter.setPen(pen)
        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )
        painter.drawPath(path)

        painter.setBrush(color)

        for index, point in enumerate(
            self._points
        ):
            value = self._clamp_percentage(
                getattr(
                    point,
                    field_name,
                    0.0,
                )
            )
            x = self._index_to_x(
                index,
                count,
                chart_rect,
            )
            y = self._value_to_y(
                value,
                chart_rect,
            )

            painter.drawEllipse(
                QPointF(
                    x,
                    y,
                ),
                3.2,
                3.2,
            )

    def _draw_legend(
        self,
        painter: QPainter,
    ) -> None:
        x = 16.0
        y = 14.0

        for (
            field_name,
            label,
            color,
        ) in self.SERIES:
            if not self._visible_series.get(
                field_name,
                False,
            ):
                continue

            painter.setPen(
                QPen(
                    color,
                    3.0,
                )
            )
            painter.drawLine(
                QPointF(
                    x,
                    y + 6,
                ),
                QPointF(
                    x + 18,
                    y + 6,
                ),
            )

            painter.setPen(
                QColor("#263238")
            )
            painter.drawText(
                QRectF(
                    x + 24,
                    y - 2,
                    110,
                    18,
                ),
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignVCenter,
                label,
            )

            x += 132.0

    @staticmethod
    def _index_to_x(
        index: int,
        count: int,
        chart_rect: QRectF,
    ) -> float:
        if count <= 1:
            return chart_rect.center().x()

        ratio = index / (count - 1)

        return (
            chart_rect.left()
            + ratio * chart_rect.width()
        )

    @staticmethod
    def _value_to_y(
        value: float,
        chart_rect: QRectF,
    ) -> float:
        ratio = OEETrendChart._clamp_percentage(
            value
        ) / 100.0

        return (
            chart_rect.bottom()
            - ratio * chart_rect.height()
        )

    @staticmethod
    def _clamp_percentage(
        value: float,
    ) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0

        return min(
            100.0,
            max(
                0.0,
                numeric,
            ),
        )
