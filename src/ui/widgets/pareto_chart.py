from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Iterable, Sequence

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True, slots=True)
class ParetoItem:
    """
    Một hạng mục dữ liệu của biểu đồ Pareto.
    """

    label: str
    value: float

    def normalized(self) -> "ParetoItem":
        label = str(self.label).strip()
        value = float(self.value)

        if not label:
            raise ValueError(
                "Pareto item label must not be empty."
            )

        if value < 0:
            raise ValueError(
                "Pareto item value must be non-negative."
            )

        return ParetoItem(
            label=label,
            value=value,
        )


@dataclass(frozen=True, slots=True)
class ParetoPoint:
    """
    Dữ liệu đã xử lý để hiển thị trên biểu đồ.
    """

    label: str
    value: float
    cumulative_value: float
    cumulative_percent: float


class ParetoChartCanvas(QWidget):
    """
    Canvas vẽ biểu đồ Pareto bằng QPainter.

    Biểu đồ gồm:
    - Cột thể hiện giá trị từng nguyên nhân.
    - Đường thể hiện tỷ lệ tích lũy.
    - Đường tham chiếu 80%.
    - Tooltip khi di chuột lên cột.
    """

    item_hovered = Signal(object)

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._points: list[ParetoPoint] = []
        self._title = "Pareto Analysis"
        self._value_axis_title = "Frequency"
        self._percent_axis_title = "Cumulative %"
        self._show_labels = True
        self._hovered_index: int | None = None
        self._bar_rectangles: list[QRectF] = []

        self.setMinimumHeight(320)
        self.setMouseTracking(True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def set_points(
        self,
        points: Sequence[ParetoPoint],
    ) -> None:
        self._points = list(points)
        self._hovered_index = None
        self._bar_rectangles = []
        self.update()

    def clear(self) -> None:
        self.set_points([])

    def set_title(
        self,
        title: str,
    ) -> None:
        self._title = str(title).strip() or "Pareto Analysis"
        self.update()

    def set_axis_titles(
        self,
        *,
        value_axis_title: str,
        percent_axis_title: str,
    ) -> None:
        self._value_axis_title = (
            str(value_axis_title).strip() or "Frequency"
        )
        self._percent_axis_title = (
            str(percent_axis_title).strip()
            or "Cumulative %"
        )
        self.update()

    def set_show_labels(
        self,
        enabled: bool,
    ) -> None:
        self._show_labels = bool(enabled)
        self.update()

    def paintEvent(
        self,
        event,
    ) -> None:
        del event

        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        self._draw_background(painter)
        self._draw_title(painter)

        if not self._points:
            self._draw_empty_state(painter)
            return

        plot_rect = self._plot_rect()

        if plot_rect.width() <= 0 or plot_rect.height() <= 0:
            return

        maximum_value = self._maximum_axis_value()
        self._draw_grid(
            painter,
            plot_rect,
            maximum_value,
        )
        self._draw_axes(
            painter,
            plot_rect,
            maximum_value,
        )
        self._draw_reference_line(
            painter,
            plot_rect,
        )
        self._draw_bars(
            painter,
            plot_rect,
            maximum_value,
        )
        self._draw_cumulative_line(
            painter,
            plot_rect,
        )
        self._draw_axis_titles(
            painter,
            plot_rect,
        )
        self._draw_tooltip(
            painter,
            plot_rect,
        )

    def mouseMoveEvent(
        self,
        event: QMouseEvent,
    ) -> None:
        hovered_index: int | None = None
        position = event.position()

        for index, rectangle in enumerate(
            self._bar_rectangles
        ):
            if rectangle.contains(position):
                hovered_index = index
                break

        if hovered_index != self._hovered_index:
            self._hovered_index = hovered_index

            if hovered_index is None:
                self.item_hovered.emit(None)
            else:
                self.item_hovered.emit(
                    self._points[hovered_index]
                )

            self.update()

        super().mouseMoveEvent(event)

    def leaveEvent(
        self,
        event,
    ) -> None:
        self._hovered_index = None
        self.item_hovered.emit(None)
        self.update()
        super().leaveEvent(event)

    def _draw_background(
        self,
        painter: QPainter,
    ) -> None:
        painter.fillRect(
            self.rect(),
            self.palette().base(),
        )

    def _draw_title(
        self,
        painter: QPainter,
    ) -> None:
        title_font = QFont(self.font())
        title_font.setBold(True)
        title_font.setPointSizeF(
            max(
                self.font().pointSizeF() + 2.0,
                11.0,
            )
        )

        painter.setFont(title_font)
        painter.setPen(
            self.palette().text().color()
        )
        painter.drawText(
            QRectF(
                16.0,
                8.0,
                max(
                    float(self.width()) - 32.0,
                    0.0,
                ),
                28.0,
            ),
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter,
            self._title,
        )

    def _draw_empty_state(
        self,
        painter: QPainter,
    ) -> None:
        painter.setPen(
            self.palette().placeholderText().color()
        )
        painter.drawText(
            self.rect().adjusted(
                20,
                40,
                -20,
                -20,
            ),
            Qt.AlignmentFlag.AlignCenter,
            "Không có dữ liệu Pareto.",
        )

    def _plot_rect(self) -> QRectF:
        left_margin = 74.0
        right_margin = 66.0
        top_margin = 52.0
        bottom_margin = (
            110.0
            if self._show_labels
            else 62.0
        )

        return QRectF(
            left_margin,
            top_margin,
            max(
                float(self.width())
                - left_margin
                - right_margin,
                0.0,
            ),
            max(
                float(self.height())
                - top_margin
                - bottom_margin,
                0.0,
            ),
        )

    def _maximum_axis_value(self) -> float:
        maximum = max(
            point.value
            for point in self._points
        )

        if maximum <= 0:
            return 1.0

        magnitude = 10 ** max(
            len(str(int(maximum))) - 1,
            0,
        )
        normalized = maximum / magnitude

        if normalized <= 1:
            step = 1
        elif normalized <= 2:
            step = 2
        elif normalized <= 5:
            step = 5
        else:
            step = 10

        return float(
            ceil(maximum / (step * magnitude))
            * step
            * magnitude
        )

    def _draw_grid(
        self,
        painter: QPainter,
        plot_rect: QRectF,
        maximum_value: float,
    ) -> None:
        del maximum_value

        grid_pen = QPen(
            self.palette().midlight().color()
        )
        grid_pen.setWidthF(1.0)
        grid_pen.setStyle(
            Qt.PenStyle.DotLine
        )

        painter.setPen(grid_pen)

        tick_count = 5

        for index in range(
            tick_count + 1
        ):
            ratio = index / tick_count
            y = (
                plot_rect.bottom()
                - ratio * plot_rect.height()
            )

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

    def _draw_axes(
        self,
        painter: QPainter,
        plot_rect: QRectF,
        maximum_value: float,
    ) -> None:
        axis_pen = QPen(
            self.palette().text().color()
        )
        axis_pen.setWidthF(1.0)
        painter.setPen(axis_pen)

        painter.drawLine(
            plot_rect.bottomLeft(),
            plot_rect.topLeft(),
        )
        painter.drawLine(
            plot_rect.bottomLeft(),
            plot_rect.bottomRight(),
        )
        painter.drawLine(
            plot_rect.bottomRight(),
            plot_rect.topRight(),
        )

        label_font = QFont(self.font())
        label_font.setPointSizeF(
            max(
                self.font().pointSizeF() - 1.0,
                8.0,
            )
        )
        painter.setFont(label_font)

        tick_count = 5

        for index in range(
            tick_count + 1
        ):
            ratio = index / tick_count
            y = (
                plot_rect.bottom()
                - ratio * plot_rect.height()
            )

            left_value = maximum_value * ratio
            right_value = 100.0 * ratio

            painter.drawText(
                QRectF(
                    4.0,
                    y - 10.0,
                    plot_rect.left() - 10.0,
                    20.0,
                ),
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter,
                self._format_number(
                    left_value
                ),
            )

            painter.drawText(
                QRectF(
                    plot_rect.right() + 8.0,
                    y - 10.0,
                    self.width()
                    - plot_rect.right()
                    - 12.0,
                    20.0,
                ),
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignVCenter,
                f"{right_value:.0f}%",
            )

    def _draw_reference_line(
        self,
        painter: QPainter,
        plot_rect: QRectF,
    ) -> None:
        y = (
            plot_rect.bottom()
            - 0.80 * plot_rect.height()
        )

        reference_pen = QPen(
            QColor(150, 150, 150)
        )
        reference_pen.setStyle(
            Qt.PenStyle.DashLine
        )
        reference_pen.setWidthF(1.25)

        painter.setPen(reference_pen)
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

        painter.drawText(
            QRectF(
                plot_rect.left() + 4.0,
                y - 20.0,
                48.0,
                18.0,
            ),
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter,
            "80%",
        )

    def _draw_bars(
        self,
        painter: QPainter,
        plot_rect: QRectF,
        maximum_value: float,
    ) -> None:
        item_count = len(self._points)
        slot_width = (
            plot_rect.width() / item_count
        )
        bar_width = max(
            min(
                slot_width * 0.62,
                54.0,
            ),
            5.0,
        )

        self._bar_rectangles = []

        normal_color = self.palette().highlight().color()
        hovered_color = normal_color.lighter(120)

        label_font = QFont(self.font())
        label_font.setPointSizeF(
            max(
                self.font().pointSizeF() - 1.5,
                7.5,
            )
        )
        painter.setFont(label_font)

        for index, point in enumerate(
            self._points
        ):
            center_x = (
                plot_rect.left()
                + slot_width * index
                + slot_width / 2.0
            )

            ratio = (
                point.value / maximum_value
                if maximum_value > 0
                else 0.0
            )
            bar_height = (
                ratio * plot_rect.height()
            )

            rectangle = QRectF(
                center_x - bar_width / 2.0,
                plot_rect.bottom() - bar_height,
                bar_width,
                bar_height,
            )
            self._bar_rectangles.append(
                rectangle
            )

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(
                hovered_color
                if index == self._hovered_index
                else normal_color
            )
            painter.drawRoundedRect(
                rectangle,
                2.5,
                2.5,
            )

            if point.value > 0:
                painter.setPen(
                    self.palette().text().color()
                )
                painter.drawText(
                    QRectF(
                        center_x
                        - slot_width / 2.0,
                        rectangle.top() - 20.0,
                        slot_width,
                        18.0,
                    ),
                    Qt.AlignmentFlag.AlignCenter,
                    self._format_number(
                        point.value
                    ),
                )

            if self._show_labels:
                self._draw_category_label(
                    painter,
                    point.label,
                    center_x,
                    plot_rect.bottom() + 8.0,
                    slot_width,
                )

    def _draw_category_label(
        self,
        painter: QPainter,
        label: str,
        center_x: float,
        top_y: float,
        slot_width: float,
    ) -> None:
        available_width = max(
            slot_width - 4.0,
            24.0,
        )
        metrics = QFontMetricsF(
            painter.font()
        )
        elided = metrics.elidedText(
            label,
            Qt.TextElideMode.ElideRight,
            int(max(available_width, 10.0)),
        )

        painter.save()
        painter.translate(
            center_x,
            top_y,
        )
        painter.rotate(-35.0)

        painter.setPen(
            self.palette().text().color()
        )
        painter.drawText(
            QRectF(
                -4.0,
                0.0,
                max(
                    available_width * 1.8,
                    60.0,
                ),
                20.0,
            ),
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter,
            elided,
        )
        painter.restore()

    def _draw_cumulative_line(
        self,
        painter: QPainter,
        plot_rect: QRectF,
    ) -> None:
        item_count = len(self._points)
        slot_width = (
            plot_rect.width() / item_count
        )

        line_color = QColor(220, 110, 35)
        line_pen = QPen(line_color)
        line_pen.setWidthF(2.25)
        painter.setPen(line_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        path = QPainterPath()

        point_positions: list[QPointF] = []

        for index, point in enumerate(
            self._points
        ):
            x = (
                plot_rect.left()
                + slot_width * index
                + slot_width / 2.0
            )
            y = (
                plot_rect.bottom()
                - (
                    point.cumulative_percent
                    / 100.0
                )
                * plot_rect.height()
            )

            position = QPointF(x, y)
            point_positions.append(position)

            if index == 0:
                path.moveTo(position)
            else:
                path.lineTo(position)

        painter.drawPath(path)

        painter.setBrush(line_color)

        for position in point_positions:
            painter.drawEllipse(
                position,
                4.0,
                4.0,
            )

    def _draw_axis_titles(
        self,
        painter: QPainter,
        plot_rect: QRectF,
    ) -> None:
        axis_font = QFont(self.font())
        axis_font.setBold(True)
        axis_font.setPointSizeF(
            max(
                self.font().pointSizeF() - 1.0,
                8.0,
            )
        )
        painter.setFont(axis_font)
        painter.setPen(
            self.palette().text().color()
        )

        painter.save()
        painter.translate(
            16.0,
            plot_rect.center().y(),
        )
        painter.rotate(-90.0)
        painter.drawText(
            QRectF(
                -plot_rect.height() / 2.0,
                -10.0,
                plot_rect.height(),
                20.0,
            ),
            Qt.AlignmentFlag.AlignCenter,
            self._value_axis_title,
        )
        painter.restore()

        painter.save()
        painter.translate(
            float(self.width()) - 16.0,
            plot_rect.center().y(),
        )
        painter.rotate(90.0)
        painter.drawText(
            QRectF(
                -plot_rect.height() / 2.0,
                -10.0,
                plot_rect.height(),
                20.0,
            ),
            Qt.AlignmentFlag.AlignCenter,
            self._percent_axis_title,
        )
        painter.restore()

    def _draw_tooltip(
        self,
        painter: QPainter,
        plot_rect: QRectF,
    ) -> None:
        if self._hovered_index is None:
            return

        if not (
            0
            <= self._hovered_index
            < len(self._points)
        ):
            return

        point = self._points[
            self._hovered_index
        ]
        bar_rect = self._bar_rectangles[
            self._hovered_index
        ]

        lines = [
            point.label,
            (
                f"Giá trị: "
                f"{self._format_number(point.value)}"
            ),
            (
                f"Tích lũy: "
                f"{point.cumulative_percent:.2f}%"
            ),
        ]

        tooltip_font = QFont(self.font())
        tooltip_font.setPointSizeF(
            max(
                self.font().pointSizeF() - 0.5,
                8.0,
            )
        )
        painter.setFont(tooltip_font)

        metrics = QFontMetricsF(
            tooltip_font
        )
        text_width = max(
            metrics.horizontalAdvance(line)
            for line in lines
        )
        line_height = metrics.height()

        tooltip_width = text_width + 20.0
        tooltip_height = (
            line_height * len(lines) + 16.0
        )

        x = min(
            bar_rect.center().x() + 10.0,
            plot_rect.right()
            - tooltip_width,
        )
        x = max(
            x,
            plot_rect.left(),
        )

        y = max(
            bar_rect.top()
            - tooltip_height
            - 8.0,
            plot_rect.top(),
        )

        tooltip_rect = QRectF(
            x,
            y,
            tooltip_width,
            tooltip_height,
        )

        painter.setPen(
            QPen(
                self.palette().mid().color()
            )
        )
        painter.setBrush(
            self.palette().toolTipBase()
        )
        painter.drawRoundedRect(
            tooltip_rect,
            5.0,
            5.0,
        )

        painter.setPen(
            self.palette().toolTipText().color()
        )

        for index, line in enumerate(lines):
            painter.drawText(
                QRectF(
                    tooltip_rect.left() + 10.0,
                    tooltip_rect.top()
                    + 8.0
                    + line_height * index,
                    tooltip_rect.width() - 20.0,
                    line_height,
                ),
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignVCenter,
                line,
            )

    @staticmethod
    def _format_number(
        value: float,
    ) -> str:
        if float(value).is_integer():
            return f"{int(value):,}"

        return f"{value:,.2f}"


class ParetoChart(QFrame):
    """
    Widget Pareto dùng chung cho Dashboard FactoryMES.

    API chính:
        set_data(items)
        set_title(title)
        set_axis_titles(...)
        clear()

    Dữ liệu đầu vào có thể là:
        ParetoItem
        tuple[str, int | float]
        dict có khóa label/name/reason và value/count/frequency
    """

    item_hovered = Signal(object)

    def __init__(
        self,
        title: str = "Pareto Analysis",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._title = title
        self._points: list[ParetoPoint] = []
        self._maximum_items: int | None = None
        self._descending = True

        self.setFrameShape(
            QFrame.Shape.StyledPanel
        )
        self.setFrameShadow(
            QFrame.Shadow.Plain
        )

        self._build_ui()
        self.set_title(title)

    @property
    def points(self) -> tuple[ParetoPoint, ...]:
        return tuple(self._points)

    def set_data(
        self,
        items: Iterable[
            ParetoItem
            | tuple[str, int | float]
            | dict[str, object]
        ],
        *,
        descending: bool = True,
        maximum_items: int | None = None,
    ) -> None:
        """
        Chuẩn hóa, sắp xếp và tính tỷ lệ tích lũy.

        maximum_items:
            Giới hạn số hạng mục hiển thị.
            Phần còn lại được gộp thành "Khác".
        """

        normalized_items = [
            self._normalize_item(item)
            for item in items
        ]

        grouped: dict[str, float] = {}

        for item in normalized_items:
            grouped[item.label] = (
                grouped.get(item.label, 0.0)
                + item.value
            )

        ordered_items = [
            ParetoItem(
                label=label,
                value=value,
            )
            for label, value in grouped.items()
        ]

        ordered_items.sort(
            key=lambda item: (
                item.value,
                item.label.casefold(),
            ),
            reverse=descending,
        )

        self._descending = bool(descending)
        self._maximum_items = maximum_items

        if maximum_items is not None:
            if maximum_items < 1:
                raise ValueError(
                    "maximum_items must be at least 1."
                )

            if len(ordered_items) > maximum_items:
                visible_count = max(
                    maximum_items - 1,
                    0,
                )
                visible_items = ordered_items[
                    :visible_count
                ]
                remaining_items = ordered_items[
                    visible_count:
                ]

                other_value = sum(
                    item.value
                    for item in remaining_items
                )

                if maximum_items == 1:
                    ordered_items = [
                        ParetoItem(
                            label="Khác",
                            value=other_value,
                        )
                    ]
                else:
                    ordered_items = [
                        *visible_items,
                        ParetoItem(
                            label="Khác",
                            value=other_value,
                        ),
                    ]

        total = sum(
            item.value
            for item in ordered_items
        )

        cumulative_value = 0.0
        points: list[ParetoPoint] = []

        for item in ordered_items:
            cumulative_value += item.value

            cumulative_percent = (
                cumulative_value / total * 100.0
                if total > 0
                else 0.0
            )

            points.append(
                ParetoPoint(
                    label=item.label,
                    value=item.value,
                    cumulative_value=cumulative_value,
                    cumulative_percent=(
                        cumulative_percent
                    ),
                )
            )

        self._points = points
        self.canvas.set_points(points)
        self._update_summary()

    def clear(self) -> None:
        self._points = []
        self.canvas.clear()
        self._update_summary()

    def set_title(
        self,
        title: str,
    ) -> None:
        self._title = (
            str(title).strip()
            or "Pareto Analysis"
        )
        self.canvas.set_title(
            self._title
        )

    def set_axis_titles(
        self,
        *,
        value_axis_title: str = "Frequency",
        percent_axis_title: str = "Cumulative %",
    ) -> None:
        self.canvas.set_axis_titles(
            value_axis_title=value_axis_title,
            percent_axis_title=percent_axis_title,
        )

    def set_show_labels(
        self,
        enabled: bool,
    ) -> None:
        self.canvas.set_show_labels(
            enabled
        )

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )
        root_layout.setSpacing(8)

        summary_layout = QHBoxLayout()
        summary_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.total_label = QLabel(
            "Tổng: 0"
        )
        self.total_label.setObjectName(
            "paretoTotalLabel"
        )

        self.focus_label = QLabel(
            "Nhóm 80%: 0"
        )
        self.focus_label.setObjectName(
            "paretoFocusLabel"
        )

        summary_layout.addWidget(
            self.total_label
        )
        summary_layout.addSpacing(16)
        summary_layout.addWidget(
            self.focus_label
        )
        summary_layout.addStretch()

        self.canvas = ParetoChartCanvas(
            self
        )
        self.canvas.item_hovered.connect(
            self.item_hovered.emit
        )

        root_layout.addLayout(
            summary_layout
        )
        root_layout.addWidget(
            self.canvas,
            1,
        )

    def _update_summary(self) -> None:
        total = sum(
            point.value
            for point in self._points
        )

        focus_count = 0

        for point in self._points:
            focus_count += 1

            if (
                point.cumulative_percent
                >= 80.0
            ):
                break

        if not self._points:
            focus_count = 0

        self.total_label.setText(
            (
                "Tổng: "
                f"{ParetoChartCanvas._format_number(total)}"
            )
        )
        self.focus_label.setText(
            f"Nhóm 80%: {focus_count}"
        )

    @staticmethod
    def _normalize_item(
        item: ParetoItem
        | tuple[str, int | float]
        | dict[str, object],
    ) -> ParetoItem:
        if isinstance(item, ParetoItem):
            return item.normalized()

        if isinstance(item, tuple):
            if len(item) != 2:
                raise ValueError(
                    (
                        "Pareto tuple item must contain "
                        "exactly two values."
                    )
                )

            return ParetoItem(
                label=str(item[0]),
                value=float(item[1]),
            ).normalized()

        if isinstance(item, dict):
            label = (
                item.get("label")
                or item.get("name")
                or item.get("reason")
                or item.get("category")
            )
            value = (
                item.get("value")
                if "value" in item
                else item.get("count")
                if "count" in item
                else item.get("frequency")
                if "frequency" in item
                else item.get("quantity")
            )

            if label is None:
                raise ValueError(
                    (
                        "Pareto dictionary item must contain "
                        "label, name, reason, or category."
                    )
                )

            if value is None:
                raise ValueError(
                    (
                        "Pareto dictionary item must contain "
                        "value, count, frequency, or quantity."
                    )
                )

            return ParetoItem(
                label=str(label),
                value=float(value),
            ).normalized()

        raise TypeError(
            (
                "Unsupported Pareto item type: "
                f"{type(item).__name__}."
            )
        )
