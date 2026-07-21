from __future__ import annotations

from typing import Any, Mapping

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class KPIValueCard(QFrame):
    """
    Thẻ hiển thị một giá trị KPI.

    Public API:
    - set_value()
    """

    def __init__(
        self,
        title: str,
        suffix: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._suffix = suffix

        self.setObjectName("kpiCard")
        self.setFrameShape(
            QFrame.Shape.StyledPanel
        )
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.setMinimumHeight(96)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            14,
            10,
            14,
            10,
        )
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName(
            "kpiCardTitle"
        )

        self.value_label = QLabel("0")
        self.value_label.setObjectName(
            "kpiCardValue"
        )
        self.value_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(
        self,
        value: int | float | str | None,
        decimals: int = 2,
    ) -> None:
        if value is None:
            text = "0"
        elif isinstance(value, bool):
            text = "1" if value else "0"
        elif isinstance(value, int):
            text = f"{value:,}"
        elif isinstance(value, float):
            text = f"{value:,.{decimals}f}"
        else:
            text = str(value)

        self.value_label.setText(
            f"{text}{self._suffix}"
        )


class OEEKPIPanel(QWidget):
    """
    Panel quản lý toàn bộ KPI của OEE Dashboard.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        layout = QGridLayout(self)
        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(10)

        self.oee_card = KPIValueCard(
            "OEE",
            "%",
        )
        self.availability_card = KPIValueCard(
            "Availability",
            "%",
        )
        self.performance_card = KPIValueCard(
            "Performance",
            "%",
        )
        self.quality_card = KPIValueCard(
            "Quality",
            "%",
        )
        self.execution_card = KPIValueCard(
            "Executions"
        )
        self.runtime_card = KPIValueCard(
            "Runtime",
            " min",
        )
        self.downtime_card = KPIValueCard(
            "Downtime",
            " min",
        )
        self.output_card = KPIValueCard(
            "OK / Total"
        )

        cards = (
            self.oee_card,
            self.availability_card,
            self.performance_card,
            self.quality_card,
            self.execution_card,
            self.runtime_card,
            self.downtime_card,
            self.output_card,
        )

        for index, card in enumerate(cards):
            row = index // 4
            column = index % 4

            layout.addWidget(
                card,
                row,
                column,
            )

        for column in range(4):
            layout.setColumnStretch(
                column,
                1,
            )

    def set_summary(
        self,
        summary: Mapping[str, Any] | None,
    ) -> None:
        data = summary or {}

        self.oee_card.set_value(
            self._number(
                data.get("oee")
            )
        )
        self.availability_card.set_value(
            self._number(
                data.get("availability")
            )
        )
        self.performance_card.set_value(
            self._number(
                data.get("performance")
            )
        )
        self.quality_card.set_value(
            self._number(
                data.get("quality")
            )
        )
        self.execution_card.set_value(
            self._integer(
                data.get("execution_count")
            ),
            decimals=0,
        )
        self.runtime_card.set_value(
            self._number(
                data.get("runtime_minutes")
            )
        )
        self.downtime_card.set_value(
            self._number(
                data.get("downtime_minutes")
            )
        )

        ok_quantity = self._integer(
            data.get("ok_quantity")
        )
        total_quantity = self._integer(
            data.get("total_quantity")
        )

        self.output_card.set_value(
            f"{ok_quantity:,} / "
            f"{total_quantity:,}"
        )

    def clear(self) -> None:
        self.set_summary({})

    @staticmethod
    def _number(
        value: Any,
    ) -> float:
        try:
            return float(value or 0)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _integer(
        value: Any,
    ) -> int:
        try:
            return int(
                round(
                    float(value or 0)
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0