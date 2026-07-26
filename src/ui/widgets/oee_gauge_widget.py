from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget


class OEEGaugeWidget(QWidget):
    """
    Lightweight OEE gauge widget.

    Public API:
        set_value(value)
        value()
        clear()

    The widget is presentation-only:
    - it does not access a database;
    - it does not call services;
    - it does not calculate OEE.
    """

    value_changed = Signal(float)

    MIN_VALUE = 0.0
    MAX_VALUE = 100.0

    GREEN_THRESHOLD = 85.0
    YELLOW_THRESHOLD = 60.0

    START_ANGLE = 225.0
    SPAN_ANGLE = -270.0

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._value = 0.0
        self._title = "OEE"
        self._suffix = "%"

        self.setMinimumSize(180, 150)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.setAccessibleName("OEE Gauge")
        self.setToolTip("Overall Equipment Effectiveness")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_value(
        self,
        value: Any,
    ) -> None:
        """
        Set the displayed OEE value.

        Accepted examples:
            82.5
            "82.5"
            "82.5%"

        Invalid, NaN and infinite values become 0.
        Values are clamped to the range 0..100.
        """

        normalized = self._normalize_value(value)

        if normalized == self._value:
            return

        self._value = normalized
        self.update()
        self.value_changed.emit(normalized)

    def value(self) -> float:
        return self._value

    def clear(self) -> None:
        self.set_value(0.0)

    def set_title(
        self,
        title: Any,
    ) -> None:
        normalized = str(
            title if title is not None else ""
        ).strip()

        if normalized == self._title:
            return

        self._title = normalized
        self.update()

    def title(self) -> str:
        return self._title

    def set_suffix(
        self,
        suffix: Any,
    ) -> None:
        normalized = str(
            suffix if suffix is not None else ""
        )

        if normalized == self._suffix:
            return

        self._suffix = normalized
        self.update()

    def suffix(self) -> str:
        return self._suffix

    # ------------------------------------------------------------------
    # Visual helpers
    # ------------------------------------------------------------------

    @classmethod
    def color_for_value(
        cls,
        value: Any,
    ) -> QColor:
        normalized = cls._normalize_value(value)

        if normalized >= cls.GREEN_THRESHOLD:
            return QColor(46, 125, 50)

        if normalized >= cls.YELLOW_THRESHOLD:
            return QColor(245, 166, 35)

        return QColor(198, 40, 40)

    @classmethod
    def status_for_value(
        cls,
        value: Any,
    ) -> str:
        normalized = cls._normalize_value(value)

        if normalized >= cls.GREEN_THRESHOLD:
            return "Good"

        if normalized >= cls.YELLOW_THRESHOLD:
            return "Warning"

        return "Critical"

    # ------------------------------------------------------------------
    # QWidget
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802
        del event

        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        side = min(
            self.width(),
            self.height(),
        )

        margin = max(
            12.0,
            side * 0.08,
        )

        gauge_rect = QRectF(
            margin,
            margin,
            self.width() - (margin * 2),
            self.height() - (margin * 2),
        )

        pen_width = max(
            10.0,
            min(
                gauge_rect.width(),
                gauge_rect.height(),
            )
            * 0.09,
        )

        self._draw_background_arc(
            painter,
            gauge_rect,
            pen_width,
        )
        self._draw_value_arc(
            painter,
            gauge_rect,
            pen_width,
        )
        self._draw_center_text(
            painter,
            gauge_rect,
        )

    def _draw_background_arc(
        self,
        painter: QPainter,
        rect: QRectF,
        pen_width: float,
    ) -> None:
        pen = QPen(
            QColor(224, 228, 233),
            pen_width,
        )
        pen.setCapStyle(
            Qt.PenCapStyle.RoundCap
        )

        painter.setPen(pen)
        painter.drawArc(
            rect,
            int(self.START_ANGLE * 16),
            int(self.SPAN_ANGLE * 16),
        )

    def _draw_value_arc(
        self,
        painter: QPainter,
        rect: QRectF,
        pen_width: float,
    ) -> None:
        progress = (
            self._value
            / self.MAX_VALUE
        )

        pen = QPen(
            self.color_for_value(
                self._value
            ),
            pen_width,
        )
        pen.setCapStyle(
            Qt.PenCapStyle.RoundCap
        )

        painter.setPen(pen)
        painter.drawArc(
            rect,
            int(self.START_ANGLE * 16),
            int(
                self.SPAN_ANGLE
                * progress
                * 16
            ),
        )

    def _draw_center_text(
        self,
        painter: QPainter,
        rect: QRectF,
    ) -> None:
        painter.setPen(
            self.palette().text().color()
        )

        value_font = QFont(
            self.font()
        )
        value_font.setBold(True)
        value_font.setPointSizeF(
            max(
                16.0,
                min(
                    rect.width(),
                    rect.height(),
                )
                * 0.12,
            )
        )

        value_rect = QRectF(
            rect.left(),
            rect.top()
            + rect.height() * 0.34,
            rect.width(),
            rect.height() * 0.25,
        )

        painter.setFont(value_font)
        painter.drawText(
            value_rect,
            Qt.AlignmentFlag.AlignCenter,
            f"{self._value:.2f}{self._suffix}",
        )

        title_font = QFont(
            self.font()
        )
        title_font.setBold(True)
        title_font.setPointSizeF(
            max(
                9.0,
                value_font.pointSizeF()
                * 0.45,
            )
        )

        title_rect = QRectF(
            rect.left(),
            value_rect.bottom(),
            rect.width(),
            rect.height() * 0.14,
        )

        painter.setFont(title_font)
        painter.drawText(
            title_rect,
            Qt.AlignmentFlag.AlignCenter,
            self._title,
        )

        status_font = QFont(
            self.font()
        )
        status_font.setPointSizeF(
            max(
                8.0,
                title_font.pointSizeF()
                * 0.85,
            )
        )

        status_rect = QRectF(
            rect.left(),
            title_rect.bottom(),
            rect.width(),
            rect.height() * 0.12,
        )

        painter.setFont(status_font)
        painter.setPen(
            self.color_for_value(
                self._value
            )
        )
        painter.drawText(
            status_rect,
            Qt.AlignmentFlag.AlignCenter,
            self.status_for_value(
                self._value
            ),
        )

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    @classmethod
    def _normalize_value(
        cls,
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
        except (TypeError, ValueError):
            return 0.0

        if number != number:
            return 0.0

        if number in (
            float("inf"),
            float("-inf"),
        ):
            return 0.0

        return max(
            cls.MIN_VALUE,
            min(
                cls.MAX_VALUE,
                number,
            ),
        )

    qt_value = Property(
        float,
        value,
        set_value,
        notify=value_changed,
    )
