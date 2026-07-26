from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from src.ui.widgets.oee_trend_widget import (
    OEETrendWidget,
    TrendPoint,
)


class OEETrendController:
    """
    Controller trung gian giữa dashboard.trend và OEETrendWidget.

    Không truy cập database, repository hoặc service.
    """

    def __init__(
        self,
        widget: OEETrendWidget,
    ) -> None:
        if not isinstance(
            widget,
            OEETrendWidget,
        ):
            raise TypeError(
                "widget must be an OEETrendWidget instance."
            )

        self._widget = widget
        self._rows: tuple[TrendPoint, ...] = ()

    @property
    def widget(self) -> OEETrendWidget:
        return self._widget

    @property
    def rows(self) -> tuple[TrendPoint, ...]:
        return self._rows

    def set_trend_data(
        self,
        rows: Iterable[Any] | None,
    ) -> tuple[TrendPoint, ...]:
        self._widget.set_data(rows)
        self._rows = self._widget.data()

        return self._rows

    def update_dashboard(
        self,
        dashboard: Any | None,
    ) -> tuple[TrendPoint, ...]:
        if dashboard is None:
            self.clear()
            return self._rows

        if not hasattr(
            dashboard,
            "trend",
        ):
            raise TypeError(
                "dashboard must provide a trend attribute."
            )

        return self.set_trend_data(
            dashboard.trend
        )

    def refresh(self) -> tuple[TrendPoint, ...]:
        self._widget.set_data(
            self._rows
        )

        return self._rows

    def clear(self) -> None:
        self._rows = ()
        self._widget.clear()