from __future__ import annotations

from typing import Any, Protocol
from src.dashboard.dashboard_logger import dashboard_logger


class DashboardLoaderProtocol(Protocol):
    """
    Giao diện tối thiểu của controller/service đang tải Dashboard.
    """

    def load_dashboard(
        self,
        filters: Any,
    ) -> Any:
        ...


class DashboardRepository:
    """
    Adapter giữa tầng ứng dụng và nguồn dữ liệu Dashboard hiện tại.

    Repository:
    - Không phụ thuộc Qt.
    - Không tính KPI.
    - Không xử lý Trend, Pareto hoặc Progress.
    - Chỉ chuyển tiếp yêu cầu tải Dashboard.
    """

    def __init__(
        self,
        loader: DashboardLoaderProtocol,
    ) -> None:
        if loader is None:
            raise ValueError(
                "loader is required."
            )

        load_dashboard = getattr(
            loader,
            "load_dashboard",
            None,
        )

        if not callable(load_dashboard):
            raise TypeError(
                "loader must provide a callable "
                "load_dashboard(filters)."
            )

        self._loader = loader

    @property
    def loader(
        self,
    ) -> DashboardLoaderProtocol:
        return self._loader

    def load(self, filters):
        dashboard_logger.info(
            "Dashboard repository load started",
            extra={
                "dashboard_component": "repository",
                "dashboard_operation": "load",
            },
        )

        try:
            result = self._loader.load_dashboard(filters)
        except Exception:
            dashboard_logger.exception(
                "Dashboard repository load failed",
                extra={
                    "dashboard_component": "repository",
                    "dashboard_operation": "load",
                },
            )
            raise

        dashboard_logger.info(
            "Dashboard repository load completed",
            extra={
                "dashboard_component": "repository",
                "dashboard_operation": "load",
            },
        )

        return result

    def refresh(
        self,
        filters: Any,
    ) -> Any:
        """
        Buộc tải lại Dashboard.

        Hiện tại refresh tương đương load. Cache sẽ được bổ sung
        ở commit tiếp theo.
        """

        return self.load(filters)