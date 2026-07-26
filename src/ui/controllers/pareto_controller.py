from __future__ import annotations

from enum import StrEnum
from typing import Any

from src.services.pareto_service import ParetoService
from src.services.ranking_service import RankingItem
from src.ui.widgets.pareto_widget import ParetoWidget


class ParetoMode(StrEnum):
    BY_MACHINE = "machine"
    BY_PRODUCT = "product"
    BY_WORK_ORDER = "work_order"
    BY_OPERATOR = "operator"
    BY_NG_TYPE = "ng_type"


class ParetoController:
    """
    Kết nối dữ liệu nguồn với ParetoService và ParetoWidget.
    """

    DEFAULT_VALUE_FIELD = "ng"

    _MODE_TITLES = {
        ParetoMode.BY_MACHINE: "Pareto NG theo máy",
        ParetoMode.BY_PRODUCT: "Pareto NG theo sản phẩm",
        ParetoMode.BY_WORK_ORDER: "Pareto NG theo công lệnh",
        ParetoMode.BY_OPERATOR: "Pareto NG theo nhân viên",
        ParetoMode.BY_NG_TYPE: "Pareto theo loại NG",
    }

    def __init__(
        self,
        widget: ParetoWidget,
        *,
        mode: ParetoMode | str = ParetoMode.BY_MACHINE,
        value_field: str = DEFAULT_VALUE_FIELD,
    ) -> None:
        if not isinstance(widget, ParetoWidget):
            raise TypeError(
                "widget must be a ParetoWidget instance."
            )

        self._widget = widget
        self._mode = self._normalize_mode(mode)
        self._value_field = self._normalize_field(
            value_field,
            field_name="value_field",
        )

        self._source_rows: tuple[Any, ...] = ()
        self._rows: tuple[RankingItem, ...] = ()

        self._apply_title()

    @property
    def widget(self) -> ParetoWidget:
        return self._widget

    @property
    def mode(self) -> ParetoMode:
        return self._mode

    @property
    def value_field(self) -> str:
        return self._value_field

    @property
    def source_rows(self) -> tuple[Any, ...]:
        return self._source_rows

    @property
    def rows(self) -> tuple[RankingItem, ...]:
        return self._rows

    def set_data(
        self,
        rows: Any,
    ) -> tuple[RankingItem, ...]:
        if rows is None:
            self.clear()
            return self._rows

        self._source_rows = tuple(rows)
        return self.refresh()

    def set_mode(
        self,
        mode: ParetoMode | str,
    ) -> tuple[RankingItem, ...]:
        normalized = self._normalize_mode(mode)

        if normalized == self._mode:
            return self._rows

        self._mode = normalized
        self._apply_title()

        if not self._source_rows:
            self._rows = ()
            self._widget.clear()
            return self._rows

        return self.refresh()

    def set_value_field(
        self,
        value_field: str,
    ) -> tuple[RankingItem, ...]:
        normalized = self._normalize_field(
            value_field,
            field_name="value_field",
        )

        if normalized == self._value_field:
            return self._rows

        self._value_field = normalized

        if not self._source_rows:
            return self._rows

        return self.refresh()

    def refresh(self) -> tuple[RankingItem, ...]:
        if not self._source_rows:
            self._rows = ()
            self._widget.clear()
            return self._rows

        self._rows = ParetoService.build(
            self._source_rows,
            group_field=self._mode.value,
            value_field=self._value_field,
        )

        self._widget.set_data(self._rows)

        return self._rows

    def clear(self) -> None:
        self._source_rows = ()
        self._rows = ()
        self._widget.clear()

    def set_title(self, title: str) -> None:
        self._widget.set_title(title)

    def _apply_title(self) -> None:
        self._widget.set_title(
            self._MODE_TITLES[self._mode]
        )

    @staticmethod
    def _normalize_mode(
        mode: ParetoMode | str,
    ) -> ParetoMode:
        if isinstance(mode, ParetoMode):
            return mode

        normalized = str(mode).strip().lower()

        aliases = {
            "machine": ParetoMode.BY_MACHINE,
            "by_machine": ParetoMode.BY_MACHINE,
            "product": ParetoMode.BY_PRODUCT,
            "by_product": ParetoMode.BY_PRODUCT,
            "work_order": ParetoMode.BY_WORK_ORDER,
            "workorder": ParetoMode.BY_WORK_ORDER,
            "by_work_order": ParetoMode.BY_WORK_ORDER,
            "operator": ParetoMode.BY_OPERATOR,
            "by_operator": ParetoMode.BY_OPERATOR,
            "ng_type": ParetoMode.BY_NG_TYPE,
            "ngtype": ParetoMode.BY_NG_TYPE,
            "by_ng_type": ParetoMode.BY_NG_TYPE,
        }

        try:
            return aliases[normalized]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported Pareto mode: {mode!r}"
            ) from exc

    @staticmethod
    def _normalize_field(
        value: str,
        *,
        field_name: str,
    ) -> str:
        normalized = str(value).strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty."
            )

        return normalized