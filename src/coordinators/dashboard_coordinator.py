from __future__ import annotations

from typing import Any, Protocol


class DashboardCacheProtocol(Protocol):
    @property
    def repository(self) -> Any:
        ...

    @property
    def has_data(self) -> bool:
        ...

    @property
    def current_data(self) -> Any | None:
        ...

    @property
    def current_filters(self) -> Any | None:
        ...

    @property
    def version(self) -> int:
        ...

    def load(self, filters: Any) -> Any:
        ...

    def refresh(self, filters: Any) -> Any:
        ...

    def invalidate(self) -> None:
        ...


class DashboardProviderProtocol(Protocol):
    @property
    def cache(self) -> DashboardCacheProtocol:
        ...

    @property
    def dashboard(self) -> Any | None:
        ...


class DashboardCoordinator:
    """
    Application Service điều phối vòng đời dữ liệu Dashboard.

    Coordinator:
    - Là API duy nhất mà tầng UI cần sử dụng.
    - Không chứa logic tính KPI.
    - Không truy cập database trực tiếp.
    - Không sửa dữ liệu Dashboard.
    - Không phụ thuộc Qt.
    """

    def __init__(
        self,
        cache: DashboardCacheProtocol,
        provider: DashboardProviderProtocol,
    ) -> None:
        if cache is None:
            raise ValueError("cache is required.")

        if provider is None:
            raise ValueError("provider is required.")

        self._validate_cache(cache)
        self._validate_provider(provider)

        if provider.cache is not cache:
            raise ValueError(
                "provider must use the same cache as coordinator."
            )

        self._cache = cache
        self._provider = provider

    @property
    def repository(self) -> Any:
        """
        Repository đang được cache sử dụng.
        """

        return self._cache.repository

    @property
    def cache(self) -> DashboardCacheProtocol:
        return self._cache

    @property
    def provider(self) -> DashboardProviderProtocol:
        return self._provider

    @property
    def has_data(self) -> bool:
        return self._cache.has_data

    @property
    def current_data(self) -> Any | None:
        return self._cache.current_data

    @property
    def current_filters(self) -> Any | None:
        return self._cache.current_filters

    @property
    def version(self) -> int:
        return self._cache.version

    def load(
        self,
        filters: Any,
    ) -> Any:
        """
        Tải dữ liệu theo cơ chế cache.

        Nếu cache đã chứa dữ liệu ứng với filter tương đương,
        DashboardDataCache sẽ trả dữ liệu hiện tại mà không gọi
        repository lần nữa.
        """

        return self._cache.load(filters)

    def refresh(
        self,
        filters: Any,
    ) -> Any:
        """
        Luôn tải dữ liệu mới từ repository thông qua cache.
        """

        return self._cache.refresh(filters)

    def invalidate(self) -> None:
        """
        Xóa snapshot hiện tại nhưng giữ lịch sử version của cache.
        """

        self._cache.invalidate()

    @staticmethod
    def _validate_cache(
        cache: DashboardCacheProtocol,
    ) -> None:
        required_members = (
            "repository",
            "has_data",
            "current_data",
            "current_filters",
            "version",
            "load",
            "refresh",
            "invalidate",
        )

        for member_name in required_members:
            if not hasattr(cache, member_name):
                raise TypeError(
                    f"cache must provide {member_name}."
                )

        for method_name in (
            "load",
            "refresh",
            "invalidate",
        ):
            if not callable(getattr(cache, method_name)):
                raise TypeError(
                    f"cache.{method_name} must be callable."
                )

    @staticmethod
    def _validate_provider(
        provider: DashboardProviderProtocol,
    ) -> None:
        if not hasattr(provider, "cache"):
            raise TypeError(
                "provider must provide cache."
            )

        if not hasattr(provider, "dashboard"):
            raise TypeError(
                "provider must provide dashboard."
            )