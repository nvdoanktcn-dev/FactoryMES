from __future__ import annotations

from typing import Any, Protocol

from src.cache.dashboard_data_cache import DashboardDataCache
from src.coordinators.dashboard_coordinator import DashboardCoordinator
from src.providers.dashboard_data_provider import DashboardDataProvider


class DashboardRepositoryProtocol(Protocol):
    def load(self, filters: Any) -> Any:
        ...


class DashboardBuilder:
    """
    Factory lắp ráp một DashboardCoordinator hoàn chỉnh từ một
    repository/loader duy nhất.

    Luồng lắp ráp:

        repository (có load(filters))
            -> DashboardDataCache   (cache 1 snapshot, quản lý version)
            -> DashboardDataProvider (đọc dữ liệu chỉ đọc từ cache)
            -> DashboardCoordinator  (API duy nhất tầng UI sử dụng)

    Đây là điểm lắp ráp duy nhất nên được dùng để tạo Dashboard
    coordinator; các thành phần con (cache/provider/coordinator)
    không nên được người gọi tự lắp ráp thủ công.
    """

    @staticmethod
    def build(
        repository: DashboardRepositoryProtocol,
    ) -> DashboardCoordinator:
        if repository is None:
            raise ValueError("repository is required.")

        cache = DashboardDataCache(repository)
        provider = DashboardDataProvider(cache)

        return DashboardCoordinator(
            cache=cache,
            provider=provider,
        )


__all__ = [
    "DashboardBuilder",
    "DashboardRepositoryProtocol",
]
