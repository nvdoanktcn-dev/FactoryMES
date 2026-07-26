from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Generic, Protocol, TypeVar
from src.dashboard.dashboard_logger import dashboard_logger


TFilter = TypeVar("TFilter")
TData = TypeVar("TData")


class DashboardRepositoryProtocol(
    Protocol[TFilter, TData],
):
    def load(
        self,
        filters: TFilter,
    ) -> TData:
        ...


@dataclass(frozen=True, slots=True)
class DashboardCacheSnapshot(
    Generic[TFilter, TData],
):
    """
    Snapshot bất biến của dữ liệu Dashboard tại một thời điểm.
    """

    filters: TFilter
    data: TData
    loaded_at: datetime
    version: int


class DashboardDataCache(
    Generic[TFilter, TData],
):
    """
    Cache một snapshot Dashboard hiện hành.

    Quy tắc:
    - load(): tái sử dụng dữ liệu nếu filters không đổi.
    - refresh(): luôn tải lại từ repository.
    - invalidate(): xóa snapshot nhưng không reset version.
    """

    def __init__(
        self,
        repository: DashboardRepositoryProtocol[
            TFilter,
            TData,
        ],
    ) -> None:
        if repository is None:
            raise ValueError(
                "repository is required."
            )

        load = getattr(
            repository,
            "load",
            None,
        )

        if not callable(load):
            raise TypeError(
                "repository must provide a callable "
                "load(filters)."
            )

        self._repository = repository
        self._snapshot: (
            DashboardCacheSnapshot[
                TFilter,
                TData,
            ]
            | None
        ) = None
        self._version = 0

    @property
    def repository(
        self,
    ) -> DashboardRepositoryProtocol[
        TFilter,
        TData,
    ]:
        return self._repository

    @property
    def has_data(
        self,
    ) -> bool:
        return self._snapshot is not None

    @property
    def current_data(
        self,
    ) -> TData | None:
        if self._snapshot is None:
            return None

        return self._snapshot.data

    @property
    def current_filters(
        self,
    ) -> TFilter | None:
        if self._snapshot is None:
            return None

        return self._snapshot.filters

    @property
    def snapshot(
        self,
    ) -> DashboardCacheSnapshot[
        TFilter,
        TData,
    ] | None:
        return self._snapshot

    @property
    def version(
        self,
    ) -> int:
        return self._version

    def load(
        self,
        filters: TFilter,
    ) -> TData:
        if self.has_data and self.current_filters == filters:
            dashboard_logger.debug(
                "Dashboard cache hit",
                extra={
                    "dashboard_component": "cache",
                    "dashboard_operation": "load",
                    "dashboard_cache_version": self.version,
                },
            )
            return self.current_data

        dashboard_logger.debug(
            "Dashboard cache miss",
            extra={
                "dashboard_component": "cache",
                "dashboard_operation": "load",
                "dashboard_cache_version": self.version,
            },
        )

        return self.refresh(filters)

    def refresh(
        self,
        filters: TFilter,
    ) -> TData:
        dashboard_logger.info(
            "Dashboard cache refresh started",
            extra={
                "dashboard_component": "cache",
                "dashboard_operation": "refresh",
                "dashboard_cache_version": self.version,
            },
        )

        dashboard_logger.info(
            "Dashboard repository load started",
            extra={
                "dashboard_component": "repository",
                "dashboard_operation": "load",
                "dashboard_cache_version": self.version,
            },
        )

        try:
            data = self._repository.load(filters)
        except Exception:
            dashboard_logger.exception(
                "Dashboard repository load failed",
                extra={
                    "dashboard_component": "repository",
                    "dashboard_operation": "load",
                    "dashboard_cache_version": self.version,
                },
            )
            dashboard_logger.exception(
                "Dashboard cache refresh failed",
                extra={
                    "dashboard_component": "cache",
                    "dashboard_operation": "refresh",
                    "dashboard_cache_version": self.version,
                },
            )
            raise

        dashboard_logger.info(
            "Dashboard repository load completed",
            extra={
                "dashboard_component": "repository",
                "dashboard_operation": "load",
                "dashboard_cache_version": self.version,
            },
        )

        # Giữ nguyên đoạn tạo snapshot hiện tại.
        self._snapshot = DashboardCacheSnapshot(
            filters=self._snapshot_filters(filters),
            data=data,
            loaded_at=datetime.now(timezone.utc),
            version=self._version + 1,
        )
        self._version += 1

        dashboard_logger.info(
            "Dashboard cache refresh completed",
            extra={
                "dashboard_component": "cache",
                "dashboard_operation": "refresh",
                "dashboard_cache_version": self.version,
            },
        )

        return data

    @staticmethod
    def _snapshot_filters(filters: TFilter) -> TFilter:
        """
        Preserve the comparison value when a mutable UI filter is
        edited in place after loading.
        """
        if not isinstance(
            filters,
            (dict, list, set),
        ):
            return filters

        try:
            return deepcopy(filters)
        except Exception:
            return filters

    def invalidate(self) -> None:
        previous_version = self.version
        had_data = self.has_data
    
        self._snapshot = None

        dashboard_logger.info(
            "Dashboard cache invalidated",
            extra={
                "dashboard_component": "cache",
                "dashboard_operation": "invalidate",
                "dashboard_cache_version": previous_version,
                "dashboard_cache_had_data": had_data,
            },
        )
