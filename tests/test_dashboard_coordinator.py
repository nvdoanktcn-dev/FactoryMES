from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any

from src.cache.dashboard_data_cache import (
    DashboardDataCache,
)
from src.coordinators.dashboard_coordinator import (
    DashboardCoordinator,
)
from src.providers.dashboard_data_provider import (
    DashboardDataProvider,
)


@dataclass(frozen=True)
class FakeFilters:
    month: int
    year: int


class FakeRepository:
    def __init__(self) -> None:
        self.load_calls: list[Any] = []
        self.results: list[Any] = []
        self.error: Exception | None = None

    def queue_result(
        self,
        result: Any,
    ) -> None:
        self.results.append(result)

    def load(
        self,
        filters: Any,
    ) -> Any:
        self.load_calls.append(filters)

        if self.error is not None:
            raise self.error

        if self.results:
            return self.results.pop(0)

        return {
            "filters": filters,
        }


class InvalidCache:
    pass


class InvalidProvider:
    pass


class TestDashboardCoordinator(
    unittest.TestCase,
):
    def create_dependencies(
        self,
    ) -> tuple[
        FakeRepository,
        DashboardDataCache,
        DashboardDataProvider,
        DashboardCoordinator,
    ]:
        repository = FakeRepository()
        cache = DashboardDataCache(repository)
        provider = DashboardDataProvider(cache)

        coordinator = DashboardCoordinator(
            cache=cache,
            provider=provider,
        )

        return (
            repository,
            cache,
            provider,
            coordinator,
        )

    def test_cache_is_required(
        self,
    ) -> None:
        repository = FakeRepository()
        cache = DashboardDataCache(repository)
        provider = DashboardDataProvider(cache)

        with self.assertRaises(ValueError):
            DashboardCoordinator(
                cache=None,  # type: ignore[arg-type]
                provider=provider,
            )

    def test_provider_is_required(
        self,
    ) -> None:
        repository = FakeRepository()
        cache = DashboardDataCache(repository)

        with self.assertRaises(ValueError):
            DashboardCoordinator(
                cache=cache,
                provider=None,  # type: ignore[arg-type]
            )

    def test_invalid_cache_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(TypeError):
            DashboardCoordinator(
                cache=InvalidCache(),  # type: ignore[arg-type]
                provider=InvalidProvider(),  # type: ignore[arg-type]
            )

    def test_invalid_provider_is_rejected(
        self,
    ) -> None:
        repository = FakeRepository()
        cache = DashboardDataCache(repository)

        with self.assertRaises(TypeError):
            DashboardCoordinator(
                cache=cache,
                provider=InvalidProvider(),  # type: ignore[arg-type]
            )

    def test_provider_must_use_same_cache(
        self,
    ) -> None:
        repository = FakeRepository()

        first_cache = DashboardDataCache(
            repository
        )
        second_cache = DashboardDataCache(
            repository
        )

        provider = DashboardDataProvider(
            second_cache
        )

        with self.assertRaises(ValueError):
            DashboardCoordinator(
                cache=first_cache,
                provider=provider,
            )

    def test_repository_property(
        self,
    ) -> None:
        repository, _, _, coordinator = (
            self.create_dependencies()
        )

        self.assertIs(
            coordinator.repository,
            repository,
        )

    def test_cache_property(
        self,
    ) -> None:
        _, cache, _, coordinator = (
            self.create_dependencies()
        )

        self.assertIs(
            coordinator.cache,
            cache,
        )

    def test_provider_property(
        self,
    ) -> None:
        _, _, provider, coordinator = (
            self.create_dependencies()
        )

        self.assertIs(
            coordinator.provider,
            provider,
        )

    def test_initial_state(
        self,
    ) -> None:
        _, _, _, coordinator = (
            self.create_dependencies()
        )

        self.assertFalse(
            coordinator.has_data
        )
        self.assertIsNone(
            coordinator.current_data
        )
        self.assertIsNone(
            coordinator.current_filters
        )
        self.assertEqual(
            coordinator.version,
            0,
        )

    def test_load_returns_repository_data(
        self,
    ) -> None:
        repository, _, _, coordinator = (
            self.create_dependencies()
        )

        filters = FakeFilters(
            month=7,
            year=2026,
        )
        expected = {
            "rows": [1, 2, 3]
        }

        repository.queue_result(expected)

        result = coordinator.load(filters)

        self.assertIs(
            result,
            expected,
        )

    def test_first_load_calls_repository(
        self,
    ) -> None:
        repository, _, _, coordinator = (
            self.create_dependencies()
        )

        filters = FakeFilters(
            month=7,
            year=2026,
        )

        coordinator.load(filters)

        self.assertEqual(
            repository.load_calls,
            [filters],
        )

    def test_load_updates_current_data(
        self,
    ) -> None:
        repository, _, _, coordinator = (
            self.create_dependencies()
        )

        filters = FakeFilters(
            month=7,
            year=2026,
        )
        expected = {
            "kpi": {"oee": 85.0}
        }

        repository.queue_result(expected)

        coordinator.load(filters)

        self.assertIs(
            coordinator.current_data,
            expected,
        )

    def test_load_updates_current_filters(
        self,
    ) -> None:
        _, _, _, coordinator = (
            self.create_dependencies()
        )

        filters = FakeFilters(
            month=7,
            year=2026,
        )

        coordinator.load(filters)

        self.assertEqual(
            coordinator.current_filters,
            filters,
        )

    def test_load_sets_has_data(
        self,
    ) -> None:
        _, _, _, coordinator = (
            self.create_dependencies()
        )

        coordinator.load(
            FakeFilters(
                month=7,
                year=2026,
            )
        )

        self.assertTrue(
            coordinator.has_data
        )

    def test_load_increments_version(
        self,
    ) -> None:
        _, _, _, coordinator = (
            self.create_dependencies()
        )

        coordinator.load(
            FakeFilters(
                month=7,
                year=2026,
            )
        )

        self.assertEqual(
            coordinator.version,
            1,
        )

    def test_same_filters_use_cached_data(
        self,
    ) -> None:
        repository, _, _, coordinator = (
            self.create_dependencies()
        )

        first_filters = FakeFilters(
            month=7,
            year=2026,
        )
        equal_filters = FakeFilters(
            month=7,
            year=2026,
        )

        first_data = {
            "version": "first"
        }
        repository.queue_result(first_data)
        repository.queue_result(
            {"version": "second"}
        )

        first_result = coordinator.load(
            first_filters
        )
        second_result = coordinator.load(
            equal_filters
        )

        self.assertIs(
            first_result,
            first_data,
        )
        self.assertIs(
            second_result,
            first_data,
        )
        self.assertEqual(
            len(repository.load_calls),
            1,
        )
        self.assertEqual(
            coordinator.version,
            1,
        )

    def test_changed_filters_reload_data(
        self,
    ) -> None:
        repository, _, _, coordinator = (
            self.create_dependencies()
        )

        first_data = {
            "month": 7
        }
        second_data = {
            "month": 8
        }

        repository.queue_result(first_data)
        repository.queue_result(second_data)

        coordinator.load(
            FakeFilters(
                month=7,
                year=2026,
            )
        )
        result = coordinator.load(
            FakeFilters(
                month=8,
                year=2026,
            )
        )

        self.assertIs(
            result,
            second_data,
        )
        self.assertEqual(
            len(repository.load_calls),
            2,
        )
        self.assertEqual(
            coordinator.version,
            2,
        )

    def test_refresh_always_calls_repository(
        self,
    ) -> None:
        repository, _, _, coordinator = (
            self.create_dependencies()
        )

        filters = FakeFilters(
            month=7,
            year=2026,
        )

        repository.queue_result(
            {"value": 1}
        )
        repository.queue_result(
            {"value": 2}
        )

        coordinator.load(filters)
        result = coordinator.refresh(filters)

        self.assertEqual(
            result,
            {"value": 2},
        )
        self.assertEqual(
            repository.load_calls,
            [filters, filters],
        )

    def test_refresh_increments_version(
        self,
    ) -> None:
        repository, _, _, coordinator = (
            self.create_dependencies()
        )

        filters = FakeFilters(
            month=7,
            year=2026,
        )

        repository.queue_result(
            {"value": 1}
        )
        repository.queue_result(
            {"value": 2}
        )

        coordinator.load(filters)
        coordinator.refresh(filters)

        self.assertEqual(
            coordinator.version,
            2,
        )

    def test_provider_reads_current_cache_data(
        self,
    ) -> None:
        repository, _, provider, coordinator = (
            self.create_dependencies()
        )

        dashboard = {
            "by_machine": [
                "BL01",
                "BL02",
            ]
        }

        repository.queue_result(dashboard)

        coordinator.load(
            FakeFilters(
                month=7,
                year=2026,
            )
        )

        self.assertIs(
            provider.dashboard,
            dashboard,
        )
        self.assertEqual(
            provider.machine_data(),
            [
                "BL01",
                "BL02",
            ],
        )

    def test_invalidate_clears_current_state(
        self,
    ) -> None:
        _, _, _, coordinator = (
            self.create_dependencies()
        )

        coordinator.load(
            FakeFilters(
                month=7,
                year=2026,
            )
        )

        coordinator.invalidate()

        self.assertFalse(
            coordinator.has_data
        )
        self.assertIsNone(
            coordinator.current_data
        )
        self.assertIsNone(
            coordinator.current_filters
        )

    def test_invalidate_preserves_version(
        self,
    ) -> None:
        _, _, _, coordinator = (
            self.create_dependencies()
        )

        coordinator.load(
            FakeFilters(
                month=7,
                year=2026,
            )
        )

        coordinator.invalidate()

        self.assertEqual(
            coordinator.version,
            1,
        )

    def test_provider_is_empty_after_invalidate(
        self,
    ) -> None:
        _, _, provider, coordinator = (
            self.create_dependencies()
        )

        coordinator.load(
            FakeFilters(
                month=7,
                year=2026,
            )
        )

        coordinator.invalidate()

        self.assertIsNone(
            provider.dashboard
        )

    def test_load_after_invalidate_reloads(
        self,
    ) -> None:
        repository, _, _, coordinator = (
            self.create_dependencies()
        )

        filters = FakeFilters(
            month=7,
            year=2026,
        )

        repository.queue_result(
            {"value": 1}
        )
        repository.queue_result(
            {"value": 2}
        )

        coordinator.load(filters)
        coordinator.invalidate()

        result = coordinator.load(filters)

        self.assertEqual(
            result,
            {"value": 2},
        )
        self.assertEqual(
            len(repository.load_calls),
            2,
        )
        self.assertEqual(
            coordinator.version,
            2,
        )

    def test_failed_refresh_preserves_previous_data(
        self,
    ) -> None:
        repository, _, provider, coordinator = (
            self.create_dependencies()
        )

        filters = FakeFilters(
            month=7,
            year=2026,
        )
        previous_data = {
            "rows": ["original"]
        }

        repository.queue_result(
            previous_data
        )
        coordinator.load(filters)

        repository.error = RuntimeError(
            "Database unavailable"
        )

        with self.assertRaises(RuntimeError):
            coordinator.refresh(filters)

        self.assertIs(
            coordinator.current_data,
            previous_data,
        )
        self.assertIs(
            provider.dashboard,
            previous_data,
        )
        self.assertEqual(
            coordinator.version,
            1,
        )

    def test_failed_first_load_keeps_empty_state(
        self,
    ) -> None:
        repository, _, _, coordinator = (
            self.create_dependencies()
        )

        repository.error = RuntimeError(
            "Database unavailable"
        )

        with self.assertRaises(RuntimeError):
            coordinator.load(
                FakeFilters(
                    month=7,
                    year=2026,
                )
            )

        self.assertFalse(
            coordinator.has_data
        )
        self.assertIsNone(
            coordinator.current_data
        )
        self.assertEqual(
            coordinator.version,
            0,
        )


if __name__ == "__main__":
    unittest.main()