from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from src.ui.controllers.oee_dashboard_controller import (
    OEEDashboardData,
)
from src.ui.widgets.top_machine_widget import (
    MachineRow,
    TopMachineWidget,
)


class TopMachineController:
    """
    Controller trung gian giữa OEEDashboardData và
    TopMachineWidget.

    Trách nhiệm:
    - Không truy cập database.
    - Không gọi OEE service.
    - Không tự tải dữ liệu Dashboard.
    - Chuyển dữ liệu by_machine sang MachineRow.
    - Cập nhật TopMachineWidget.
    """

    def __init__(
        self,
        widget: TopMachineWidget,
    ) -> None:
        if not isinstance(widget, TopMachineWidget):
            raise TypeError(
                "widget must be a TopMachineWidget instance."
            )

        self._widget = widget
        self._rows: list[MachineRow] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def widget(self) -> TopMachineWidget:
        return self._widget

    @property
    def rows(self) -> tuple[MachineRow, ...]:
        """
        Trả về snapshot chỉ đọc của dữ liệu hiện tại.
        """

        return tuple(self._rows)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_dashboard(
        self,
        dashboard: OEEDashboardData | None,
    ) -> list[MachineRow]:
        """
        Cập nhật widget từ OEEDashboardData.

        Args:
            dashboard:
                Dữ liệu Dashboard đã được tải bởi
                OEEDashboardController.

        Returns:
            Danh sách MachineRow đã chuẩn hóa.
        """

        if dashboard is None:
            self.clear()
            return []

        if not isinstance(dashboard, OEEDashboardData):
            raise TypeError(
                "dashboard must be an OEEDashboardData instance "
                "or None."
            )

        return self.set_machine_data(
            dashboard.by_machine
        )

    def set_machine_data(
        self,
        rows: Iterable[Any] | None,
    ) -> list[MachineRow]:
        """
        Cập nhật widget trực tiếp từ danh sách breakdown theo máy.

        Hàm này hữu ích cho unit test và cho các trường hợp UI đã
        có sẵn dữ liệu by_machine mà không cần truyền toàn bộ
        OEEDashboardData.
        """

        if rows is None:
            self.clear()
            return []

        normalized_rows = [
            self._convert_row(row)
            for row in rows
        ]

        self._rows = normalized_rows
        self._widget.set_data(normalized_rows)

        return list(normalized_rows)

    def refresh(self) -> None:
        """
        Yêu cầu widget hiển thị lại dữ liệu hiện tại.
        """

        self._widget.set_data(self._rows)

    def clear(self) -> None:
        """
        Xóa dữ liệu controller và widget.
        """

        self._rows.clear()
        self._widget.set_data([])

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def _convert_row(
        self,
        row: Any,
    ) -> MachineRow:
        if isinstance(row, MachineRow):
            return row

        if isinstance(row, Mapping):
            return self._from_mapping(row)

        return self._from_object(row)

    def _from_mapping(
        self,
        row: Mapping[str, Any],
    ) -> MachineRow:
        machine = self._first_text(
            row,
            "machine",
            "machine_code",
            "group_label",
            "group_key",
        )

        return MachineRow(
            machine=machine,
            oee=self._to_float(
                row.get("oee")
            ),
            availability=self._to_float(
                row.get("availability")
            ),
            performance=self._to_float(
                row.get("performance")
            ),
            quality=self._to_float(
                row.get("quality")
            ),
            runtime=self._to_float(
                self._first_value(
                    row,
                    "runtime",
                    "runtime_minutes",
                )
            ),
            downtime=self._to_float(
                self._first_value(
                    row,
                    "downtime",
                    "downtime_minutes",
                )
            ),
            ok_qty=self._to_int(
                self._first_value(
                    row,
                    "ok_qty",
                    "ok_quantity",
                )
            ),
            ng_qty=self._to_int(
                self._first_value(
                    row,
                    "ng_qty",
                    "ng_quantity",
                )
            ),
        )

    def _from_object(
        self,
        row: Any,
    ) -> MachineRow:
        machine = self._first_attribute_text(
            row,
            "machine",
            "machine_code",
            "group_label",
            "group_key",
        )

        return MachineRow(
            machine=machine,
            oee=self._to_float(
                getattr(row, "oee", None)
            ),
            availability=self._to_float(
                getattr(row, "availability", None)
            ),
            performance=self._to_float(
                getattr(row, "performance", None)
            ),
            quality=self._to_float(
                getattr(row, "quality", None)
            ),
            runtime=self._to_float(
                self._first_attribute_value(
                    row,
                    "runtime",
                    "runtime_minutes",
                )
            ),
            downtime=self._to_float(
                self._first_attribute_value(
                    row,
                    "downtime",
                    "downtime_minutes",
                )
            ),
            ok_qty=self._to_int(
                self._first_attribute_value(
                    row,
                    "ok_qty",
                    "ok_quantity",
                )
            ),
            ng_qty=self._to_int(
                self._first_attribute_value(
                    row,
                    "ng_qty",
                    "ng_quantity",
                )
            ),
        )

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _first_value(
        row: Mapping[str, Any],
        *keys: str,
    ) -> Any:
        for key in keys:
            value = row.get(key)

            if value is not None:
                return value

        return None

    @classmethod
    def _first_text(
        cls,
        row: Mapping[str, Any],
        *keys: str,
    ) -> str:
        value = cls._first_value(
            row,
            *keys,
        )

        return cls._to_text(value)

    # ------------------------------------------------------------------
    # Object helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _first_attribute_value(
        row: Any,
        *attribute_names: str,
    ) -> Any:
        for attribute_name in attribute_names:
            value = getattr(
                row,
                attribute_name,
                None,
            )

            if value is not None:
                return value

        return None

    @classmethod
    def _first_attribute_text(
        cls,
        row: Any,
        *attribute_names: str,
    ) -> str:
        value = cls._first_attribute_value(
            row,
            *attribute_names,
        )

        return cls._to_text(value)

    # ------------------------------------------------------------------
    # Type conversion
    # ------------------------------------------------------------------

    @staticmethod
    def _to_text(
        value: Any,
    ) -> str:
        if value is None:
            return ""

        return str(value).strip()

    @staticmethod
    def _to_float(
        value: Any,
    ) -> float:
        if value is None:
            return 0.0

        if isinstance(value, str):
            cleaned = (
                value.strip()
                .replace(",", "")
                .replace("%", "")
            )

            if not cleaned:
                return 0.0

            value = cleaned

        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _to_int(
        value: Any,
    ) -> int:
        if value is None:
            return 0

        if isinstance(value, str):
            cleaned = (
                value.strip()
                .replace(",", "")
            )

            if not cleaned:
                return 0

            value = cleaned

        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0