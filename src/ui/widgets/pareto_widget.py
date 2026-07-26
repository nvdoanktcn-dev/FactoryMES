from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.services.ranking_service import RankingItem


class _ParetoCanvas(QWidget):
    """
    Canvas vẽ biểu đồ Pareto:

    - Cột: giá trị tuyệt đối
    - Đường: tỷ lệ tích lũy
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._rows: tuple[RankingItem, ...] = ()

        self.setMinimumHeight(300)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def set_data(
        self,
        rows: tuple[RankingItem, ...],
    ) -> None:
        self._rows = rows
        self.update()

    def clear(self) -> None:
        self._rows = ()
        self.update()

    def paintEvent(self, event: Any) -> None:
        del event

        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        painter.fillRect(
            self.rect(),
            QColor("#FFFFFF"),
        )

        if not self._rows:
            self._draw_empty_state(painter)
            return

        self._draw_chart(painter)

    def _draw_empty_state(
        self,
        painter: QPainter,
    ) -> None:
        painter.setPen(
            QColor("#808080")
        )

        font = QFont()
        font.setPointSize(11)
        painter.setFont(font)

        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "No Pareto data",
        )

    def _draw_chart(
        self,
        painter: QPainter,
    ) -> None:
        width = float(self.width())
        height = float(self.height())

        left_margin = 58.0
        right_margin = 58.0
        top_margin = 28.0
        bottom_margin = 70.0

        chart_left = left_margin
        chart_top = top_margin
        chart_right = max(
            chart_left + 1.0,
            width - right_margin,
        )
        chart_bottom = max(
            chart_top + 1.0,
            height - bottom_margin,
        )

        chart_width = (
            chart_right - chart_left
        )
        chart_height = (
            chart_bottom - chart_top
        )

        max_value = max(
            (
                row.value
                for row in self._rows
            ),
            default=0.0,
        )

        if max_value <= 0:
            max_value = 1.0

        self._draw_grid(
            painter=painter,
            chart_left=chart_left,
            chart_top=chart_top,
            chart_right=chart_right,
            chart_bottom=chart_bottom,
            max_value=max_value,
        )

        count = len(self._rows)

        slot_width = chart_width / max(
            count,
            1,
        )

        bar_width = min(
            slot_width * 0.62,
            54.0,
        )

        cumulative_points: list[QPointF] = []

        for index, row in enumerate(
            self._rows
        ):
            center_x = (
                chart_left
                + slot_width * index
                + slot_width / 2.0
            )

            bar_height = (
                row.value
                / max_value
                * chart_height
            )

            bar_rect = QRectF(
                center_x - bar_width / 2.0,
                chart_bottom - bar_height,
                bar_width,
                bar_height,
            )

            self._draw_bar(
                painter,
                bar_rect,
                row,
            )

            cumulative_y = (
                chart_bottom
                - (
                    row.cumulative_percent
                    / 100.0
                    * chart_height
                )
            )

            cumulative_points.append(
                QPointF(
                    center_x,
                    cumulative_y,
                )
            )

            self._draw_category_label(
                painter=painter,
                center_x=center_x,
                chart_bottom=chart_bottom,
                slot_width=slot_width,
                text=row.name,
            )

        self._draw_cumulative_line(
            painter,
            cumulative_points,
        )

        self._draw_axis_titles(
            painter=painter,
            chart_left=chart_left,
            chart_top=chart_top,
            chart_right=chart_right,
            chart_bottom=chart_bottom,
        )

    def _draw_grid(
        self,
        *,
        painter: QPainter,
        chart_left: float,
        chart_top: float,
        chart_right: float,
        chart_bottom: float,
        max_value: float,
    ) -> None:
        chart_height = (
            chart_bottom - chart_top
        )

        grid_pen = QPen(
            QColor("#E3E7EC")
        )
        grid_pen.setWidthF(1.0)

        axis_pen = QPen(
            QColor("#69727D")
        )
        axis_pen.setWidthF(1.2)

        label_font = QFont()
        label_font.setPointSize(8)
        painter.setFont(label_font)

        grid_steps = 5

        for step in range(
            grid_steps + 1
        ):
            ratio = (
                step / grid_steps
            )

            y = (
                chart_bottom
                - ratio * chart_height
            )

            painter.setPen(grid_pen)
            painter.drawLine(
                QPointF(
                    chart_left,
                    y,
                ),
                QPointF(
                    chart_right,
                    y,
                ),
            )

            value_label = (
                max_value * ratio
            )

            painter.setPen(
                QColor("#59636E")
            )
            painter.drawText(
                QRectF(
                    0,
                    y - 10,
                    chart_left - 8,
                    20,
                ),
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter,
                self._format_number(
                    value_label
                ),
            )

            percent_label = (
                ratio * 100
            )

            painter.drawText(
                QRectF(
                    chart_right + 8,
                    y - 10,
                    48,
                    20,
                ),
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignVCenter,
                f"{percent_label:.0f}%",
            )

        painter.setPen(axis_pen)

        painter.drawLine(
            QPointF(
                chart_left,
                chart_top,
            ),
            QPointF(
                chart_left,
                chart_bottom,
            ),
        )

        painter.drawLine(
            QPointF(
                chart_left,
                chart_bottom,
            ),
            QPointF(
                chart_right,
                chart_bottom,
            ),
        )

        painter.drawLine(
            QPointF(
                chart_right,
                chart_top,
            ),
            QPointF(
                chart_right,
                chart_bottom,
            ),
        )

    def _draw_bar(
        self,
        painter: QPainter,
        rect: QRectF,
        row: RankingItem,
    ) -> None:
        painter.setPen(
            Qt.PenStyle.NoPen
        )
        painter.setBrush(
            QColor("#4A90E2")
        )
        painter.drawRoundedRect(
            rect,
            3.0,
            3.0,
        )

        if rect.height() < 20:
            return

        value_font = QFont()
        value_font.setPointSize(8)
        value_font.setBold(True)

        painter.setFont(value_font)
        painter.setPen(
            QColor("#FFFFFF")
        )

        painter.drawText(
            rect.adjusted(
                2,
                3,
                -2,
                -3,
            ),
            Qt.AlignmentFlag.AlignTop
            | Qt.AlignmentFlag.AlignHCenter,
            self._format_number(
                row.value
            ),
        )

    def _draw_cumulative_line(
        self,
        painter: QPainter,
        points: list[QPointF],
    ) -> None:
        if not points:
            return

        line_pen = QPen(
            QColor("#E67E22")
        )
        line_pen.setWidthF(2.2)

        painter.setPen(line_pen)
        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        path = QPainterPath()
        path.moveTo(points[0])

        for point in points[1:]:
            path.lineTo(point)

        painter.drawPath(path)

        for point in points:
            painter.setPen(
                QPen(
                    QColor("#E67E22"),
                    1.5,
                )
            )
            painter.setBrush(
                QColor("#FFFFFF")
            )
            painter.drawEllipse(
                point,
                4.0,
                4.0,
            )

    def _draw_category_label(
        self,
        *,
        painter: QPainter,
        center_x: float,
        chart_bottom: float,
        slot_width: float,
        text: str,
    ) -> None:
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(
            QColor("#38414A")
        )

        label_width = max(
            slot_width,
            40.0,
        )

        label_rect = QRectF(
            center_x - label_width / 2.0,
            chart_bottom + 6,
            label_width,
            42,
        )

        painter.save()

        if slot_width < 70:
            painter.translate(
                label_rect.center()
            )
            painter.rotate(-35)

            rotated_rect = QRectF(
                -label_width / 2.0,
                -10,
                label_width,
                20,
            )

            painter.drawText(
                rotated_rect,
                Qt.AlignmentFlag.AlignCenter,
                self._shorten_label(
                    text,
                    14,
                ),
            )
        else:
            painter.drawText(
                label_rect,
                Qt.AlignmentFlag.AlignTop
                | Qt.AlignmentFlag.AlignHCenter,
                self._shorten_label(
                    text,
                    18,
                ),
            )

        painter.restore()

    def _draw_axis_titles(
        self,
        *,
        painter: QPainter,
        chart_left: float,
        chart_top: float,
        chart_right: float,
        chart_bottom: float,
    ) -> None:
        title_font = QFont()
        title_font.setPointSize(8)
        title_font.setBold(True)

        painter.setFont(title_font)
        painter.setPen(
            QColor("#59636E")
        )

        painter.drawText(
            QRectF(
                chart_left,
                2,
                160,
                20,
            ),
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter,
            "Quantity",
        )

        painter.drawText(
            QRectF(
                chart_right - 160,
                2,
                160,
                20,
            ),
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter,
            "Cumulative %",
        )

        painter.drawText(
            QRectF(
                chart_left,
                chart_bottom + 48,
                chart_right - chart_left,
                20,
            ),
            Qt.AlignmentFlag.AlignCenter,
            "Category",
        )

    @staticmethod
    def _format_number(
        value: float,
    ) -> str:
        if float(value).is_integer():
            return f"{int(value):,}"

        return f"{value:,.2f}"

    @staticmethod
    def _shorten_label(
        text: str,
        limit: int,
    ) -> str:
        normalized = str(text).strip()

        if len(normalized) <= limit:
            return normalized

        return (
            normalized[: limit - 1]
            + "…"
        )


class ParetoWidget(QWidget):
    """
    Widget hiển thị biểu đồ Pareto.

    Dữ liệu chuẩn:

        RankingItem(
            name,
            value,
            percent,
            cumulative_percent,
            rank,
        )

    Widget cũng hỗ trợ dict và object có các thuộc tính tương ứng.
    """

    DEFAULT_TITLE = "Pareto Analysis"

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._title = (
            self.DEFAULT_TITLE
        )
        self._rows: tuple[
            RankingItem,
            ...
        ] = ()

        self._canvas = _ParetoCanvas(
            self
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        layout.setSpacing(0)
        layout.addWidget(
            self._canvas
        )

    def set_title(
        self,
        title: str,
    ) -> None:
        self._title = str(
            title
        ).strip()
        self.setToolTip(
            self._title
        )
        self.update()

    def title(self) -> str:
        return self._title

    def set_data(
        self,
        rows: Iterable[Any] | None,
    ) -> None:
        if rows is None:
            self.clear()
            return

        normalized_rows: list[
            RankingItem
        ] = []

        for index, row in enumerate(
            rows,
            start=1,
        ):
            normalized_rows.append(
                self._normalize_row(
                    row,
                    default_rank=index,
                )
            )

        self._rows = tuple(
            normalized_rows
        )

        self._canvas.set_data(
            self._rows
        )

    def data(
        self,
    ) -> tuple[RankingItem, ...]:
        return self._rows

    def point_count(self) -> int:
        return len(
            self._rows
        )

    def clear(self) -> None:
        self._rows = ()
        self._canvas.clear()

    @classmethod
    def _normalize_row(
        cls,
        row: Any,
        *,
        default_rank: int,
    ) -> RankingItem:
        if isinstance(
            row,
            RankingItem,
        ):
            return RankingItem(
                name=str(row.name),
                value=cls._normalize_value(
                    row.value
                ),
                percent=cls._normalize_percent(
                    row.percent
                ),
                cumulative_percent=(
                    cls._normalize_percent(
                        row.cumulative_percent
                    )
                ),
                rank=cls._normalize_rank(
                    row.rank,
                    default_rank,
                ),
            )

        if isinstance(
            row,
            Mapping,
        ):
            getter = row.get
        else:
            getter = lambda key, default=None: getattr(
                row,
                key,
                default,
            )

        name = str(
            getter(
                "name",
                "",
            )
        ).strip()

        value = cls._normalize_value(
            getter(
                "value",
                0,
            )
        )

        percent = cls._normalize_percent(
            getter(
                "percent",
                0,
            )
        )

        cumulative_percent = (
            cls._normalize_percent(
                getter(
                    "cumulative_percent",
                    0,
                )
            )
        )

        rank = cls._normalize_rank(
            getter(
                "rank",
                default_rank,
            ),
            default_rank,
        )

        return RankingItem(
            name=name,
            value=value,
            percent=percent,
            cumulative_percent=(
                cumulative_percent
            ),
            rank=rank,
        )

    @staticmethod
    def _normalize_value(
        value: Any,
    ) -> float:
        if value is None:
            return 0.0

        if isinstance(
            value,
            str,
        ):
            value = (
                value.strip()
                .replace(",", "")
            )

            if value.endswith("%"):
                value = value[:-1]

        try:
            normalized = float(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

        if not math.isfinite(
            normalized
        ):
            return 0.0

        return max(
            normalized,
            0.0,
        )

    @classmethod
    def _normalize_percent(
        cls,
        value: Any,
    ) -> float:
        normalized = (
            cls._normalize_value(
                value
            )
        )

        return min(
            normalized,
            100.0,
        )

    @staticmethod
    def _normalize_rank(
        value: Any,
        default: int,
    ) -> int:
        if isinstance(
            value,
            bool,
        ):
            return default

        try:
            normalized = int(value)
        except (
            TypeError,
            ValueError,
        ):
            return default

        if normalized < 1:
            return default

        return normalized