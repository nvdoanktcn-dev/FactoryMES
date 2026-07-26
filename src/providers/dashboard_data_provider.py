from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Protocol


class DashboardCacheProtocol(Protocol):
    @property
    def current_data(
        self,
    ) -> Any | None:
        ...


class DashboardDataProvider:
    """
    Cung cấp các lát dữ liệu chỉ đọc từ Dashboard cache.

    Provider:
    - Không gọi repository.
    - Không refresh cache.
    - Không sửa DashboardData.
    - Không phụ thuộc Qt.
    """

    _BREAKDOWN_ALIASES: dict[
        str,
        tuple[str, ...],
    ] = {
        "machine": (
            "by_machine",
            "machines",
        ),
        "employee": (
            "by_employee",
            "employees",
        ),
        "work_order": (
            "by_work_order",
            "work_orders",
        ),
        "product": (
            "by_product",
            "products",
        ),
        "operation": (
            "by_operation",
            "operations",
        ),
    }

    def __init__(
        self,
        cache: DashboardCacheProtocol,
    ) -> None:
        if cache is None:
            raise ValueError(
                "cache is required."
            )

        if not hasattr(
            cache,
            "current_data",
        ):
            raise TypeError(
                "cache must provide current_data."
            )

        self._cache = cache

    @property
    def cache(
        self,
    ) -> DashboardCacheProtocol:
        return self._cache

    @property
    def dashboard(
        self,
    ) -> Any | None:
        return self._cache.current_data

    def require_dashboard(
        self,
    ) -> Any:
        """
        Trả Dashboard hiện hành hoặc báo lỗi nếu cache rỗng.
        """

        data = self.dashboard

        if data is None:
            raise RuntimeError(
                "Dashboard cache does not contain data."
            )

        return data

    def kpi_data(
        self,
    ) -> Any:
        """
        Trả dữ liệu KPI.

        Thứ tự ưu tiên:
        1. kpi
        2. summary
        3. overall
        4. chính DashboardData
        """

        data = self.require_dashboard()

        for attribute_name in (
            "kpi",
            "summary",
            "overall",
        ):
            value = self._read_value(
                data,
                attribute_name,
            )

            if value is not None:
                return value

        return data

    def machine_data(
        self,
    ) -> list[Any]:
        """
        Trả dữ liệu Top Machine hoặc breakdown theo máy.
        """

        return self._first_sequence(
            "top_machines",
            "top_machine",
            "by_machine",
            "machines",
        )

    def pareto_data(
        self,
    ) -> list[Any]:
        """
        Trả dữ liệu Pareto NG.
        """

        return self._first_sequence(
            "pareto",
            "pareto_rows",
            "ng_pareto",
            "defect_pareto",
        )

    def trend_data(
        self,
    ) -> list[Any]:
        """
        Trả nguồn dữ liệu chi tiết cho TrendService.
        """

        return self._first_sequence(
            "trend",
            "trend_rows",
            "execution_rows",
            "executions",
            "detail_rows",
            "details",
            "raw_rows",
            "rows",
        )

    def progress_data(
        self,
    ) -> list[Any]:
        """
        Trả nguồn dữ liệu tiến độ công lệnh.
        """

        return self._first_sequence(
            "progress",
            "progress_rows",
            "by_work_order",
            "work_orders",
        )

    def breakdown_data(
        self,
        name: str,
    ) -> list[Any]:
        """
        Trả breakdown theo tên chuẩn.

        Tên hỗ trợ:
        - machine
        - employee
        - work_order
        - product
        - operation
        """

        normalized_name = str(
            name
        ).strip().lower()

        attribute_names = (
            self._BREAKDOWN_ALIASES.get(
                normalized_name
            )
        )

        if attribute_names is None:
            raise ValueError(
                f"Unsupported breakdown: {name}"
            )

        return self._first_sequence(
            *attribute_names
        )

    def _first_sequence(
        self,
        *attribute_names: str,
    ) -> list[Any]:
        """
        Trả sequence đầu tiên tồn tại theo thứ tự ưu tiên.
        """

        data = self.require_dashboard()

        for attribute_name in attribute_names:
            value = self._read_value(
                data,
                attribute_name,
            )

            normalized = (
                self._normalize_sequence(
                    value
                )
            )

            if normalized is not None:
                return normalized

        return []

    @staticmethod
    def _read_value(
        source: Any,
        name: str,
    ) -> Any:
        """
        Hỗ trợ cả object model và mapping.
        """

        if isinstance(
            source,
            Mapping,
        ):
            return source.get(name)

        return getattr(
            source,
            name,
            None,
        )

    @staticmethod
    def _normalize_sequence(
        value: Any,
    ) -> list[Any] | None:
        """
        Chuẩn hóa sequence thành list.

        None nghĩa là thuộc tính không có dữ liệu phù hợp.
        Danh sách rỗng vẫn là dữ liệu hợp lệ.
        """

        if value is None:
            return None

        if isinstance(
            value,
            list,
        ):
            return value

        if isinstance(
            value,
            tuple,
        ):
            return list(value)

        if isinstance(
            value,
            Mapping,
        ):
            return None

        if isinstance(
            value,
            (str, bytes),
        ):
            return None

        if isinstance(
            value,
            Iterable,
        ):
            return list(value)

        return None