from __future__ import annotations

import unittest
from datetime import timezone
from unittest.mock import Mock

from src.cache.dashboard_data_cache import (
    DashboardCacheSnapshot,
    DashboardDataCache,
)


class TestDashboardDataCache(
    unittest.TestCase,
):
    def setUp(
        self,
    ) -> None:
        self.repository = Mock()
        self.cache = DashboardDataCache(
            self.repository
        )

    def test_repository_is_required(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            DashboardDataCache(
                None  # type: ignore[arg-type]
            )

    def test_repository_must_have_load(
        self,
    ) -> None:
        with self.assertRaises(TypeError):
            DashboardDataCache(
                object()  # type: ignore[arg-type]
            )

    def test_initial_state_is_empty(
        self,
    ) -> None:
        self.assertFalse(
            self.cache.has_data
        )
        self.assertIsNone(
            self.cache.current_data
        )
        self.assertIsNone(
            self.cache.current_filters
        )
        self.assertIsNone(
            self.cache.snapshot
        )
        self.assertEqual(
            self.cache.version,
            0,
        )

    def test_repository_property(
        self,
    ) -> None:
        self.assertIs(
            self.cache.repository,
            self.repository,
        )

    def test_first_load_calls_repository(
        self,
    ) -> None:
        filters = object()
        expected = object()

        self.repository.load.return_value = (
            expected
        )

        result = self.cache.load(
            filters
        )

        self.assertIs(
            result,
            expected,
        )
        self.assertTrue(
            self.cache.has_data
        )
        self.assertIs(
            self.cache.current_data,
            expected,
        )
        self.assertIs(
            self.cache.current_filters,
            filters,
        )

        self.repository.load.assert_called_once_with(
            filters
        )

    def test_load_same_filters_uses_cache(
        self,
    ) -> None:
        filters = object()
        expected = object()

        self.repository.load.return_value = (
            expected
        )

        first = self.cache.load(
            filters
        )
        second = self.cache.load(
            filters
        )

        self.assertIs(
            first,
            expected,
        )
        self.assertIs(
            second,
            expected,
        )

        self.repository.load.assert_called_once_with(
            filters
        )

    def test_load_equal_filters_uses_cache(
        self,
    ) -> None:
        first_filters = {
            "machine": "BL01",
            "month": 7,
        }
        equal_filters = {
            "machine": "BL01",
            "month": 7,
        }

        self.repository.load.return_value = (
            "dashboard"
        )

        self.cache.load(
            first_filters
        )
        result = self.cache.load(
            equal_filters
        )

        self.assertEqual(
            result,
            "dashboard",
        )
        self.assertEqual(
            self.repository.load.call_count,
            1,
        )

    def test_changed_filters_reload_repository(
        self,
    ) -> None:
        self.repository.load.side_effect = [
            "dashboard-a",
            "dashboard-b",
        ]

        first = self.cache.load(
            "filters-a"
        )
        second = self.cache.load(
            "filters-b"
        )

        self.assertEqual(
            first,
            "dashboard-a",
        )
        self.assertEqual(
            second,
            "dashboard-b",
        )
        self.assertEqual(
            self.repository.load.call_count,
            2,
        )
        self.assertEqual(
            self.cache.current_filters,
            "filters-b",
        )
        self.assertEqual(
            self.cache.current_data,
            "dashboard-b",
        )

    def test_mutating_original_filters_causes_reload(
        self,
    ) -> None:
        filters = {
            "machine": "BL01",
        }
        self.repository.load.side_effect = [
            {"version": 1},
            {"version": 2},
        ]

        first = self.cache.load(filters)
        filters["machine"] = "BL02"
        second = self.cache.load(filters)

        self.assertEqual(
            self.repository.load.call_count,
            2,
        )
        self.assertEqual(first, {"version": 1})
        self.assertEqual(second, {"version": 2})
        self.assertEqual(
            self.cache.current_filters,
            {"machine": "BL02"},
        )

    def test_refresh_always_calls_repository(
        self,
    ) -> None:
        self.repository.load.side_effect = [
            "dashboard-1",
            "dashboard-2",
        ]

        first = self.cache.refresh(
            "filters"
        )
        second = self.cache.refresh(
            "filters"
        )

        self.assertEqual(
            first,
            "dashboard-1",
        )
        self.assertEqual(
            second,
            "dashboard-2",
        )
        self.assertEqual(
            self.repository.load.call_count,
            2,
        )
        self.assertEqual(
            self.cache.version,
            2,
        )

    def test_snapshot_contains_metadata(
        self,
    ) -> None:
        filters = object()
        data = object()

        self.repository.load.return_value = (
            data
        )

        self.cache.load(
            filters
        )

        snapshot = self.cache.snapshot

        self.assertIsInstance(
            snapshot,
            DashboardCacheSnapshot,
        )

        assert snapshot is not None

        self.assertIs(
            snapshot.filters,
            filters,
        )
        self.assertIs(
            snapshot.data,
            data,
        )
        self.assertEqual(
            snapshot.version,
            1,
        )
        self.assertEqual(
            snapshot.loaded_at.tzinfo,
            timezone.utc,
        )

    def test_version_increases_after_reload(
        self,
    ) -> None:
        self.repository.load.side_effect = [
            "one",
            "two",
            "three",
        ]

        self.cache.load(
            "filters-a"
        )
        self.assertEqual(
            self.cache.version,
            1,
        )

        self.cache.load(
            "filters-b"
        )
        self.assertEqual(
            self.cache.version,
            2,
        )

        self.cache.refresh(
            "filters-b"
        )
        self.assertEqual(
            self.cache.version,
            3,
        )

    def test_cached_load_does_not_increment_version(
        self,
    ) -> None:
        self.repository.load.return_value = (
            "dashboard"
        )

        self.cache.load(
            "filters"
        )
        initial_version = (
            self.cache.version
        )

        self.cache.load(
            "filters"
        )

        self.assertEqual(
            self.cache.version,
            initial_version,
        )

    def test_invalidate_clears_snapshot(
        self,
    ) -> None:
        self.repository.load.return_value = (
            "dashboard"
        )

        self.cache.load(
            "filters"
        )

        self.cache.invalidate()

        self.assertFalse(
            self.cache.has_data
        )
        self.assertIsNone(
            self.cache.current_data
        )
        self.assertIsNone(
            self.cache.current_filters
        )
        self.assertIsNone(
            self.cache.snapshot
        )

    def test_invalidate_does_not_reset_version(
        self,
    ) -> None:
        self.repository.load.return_value = (
            "dashboard"
        )

        self.cache.load(
            "filters"
        )

        self.cache.invalidate()

        self.assertEqual(
            self.cache.version,
            1,
        )

    def test_load_after_invalidate_calls_repository_again(
        self,
    ) -> None:
        self.repository.load.side_effect = [
            "first",
            "second",
        ]

        self.cache.load(
            "filters"
        )
        self.cache.invalidate()

        result = self.cache.load(
            "filters"
        )

        self.assertEqual(
            result,
            "second",
        )
        self.assertEqual(
            self.repository.load.call_count,
            2,
        )
        self.assertEqual(
            self.cache.version,
            2,
        )

    def test_repository_exception_does_not_replace_snapshot(
        self,
    ) -> None:
        self.repository.load.return_value = (
            "valid-dashboard"
        )

        self.cache.load(
            "filters-a"
        )

        original_snapshot = (
            self.cache.snapshot
        )

        self.repository.load.side_effect = (
            RuntimeError("database error")
        )

        with self.assertRaises(RuntimeError):
            self.cache.refresh(
                "filters-b"
            )

        self.assertIs(
            self.cache.snapshot,
            original_snapshot,
        )
        self.assertEqual(
            self.cache.current_data,
            "valid-dashboard",
        )
        self.assertEqual(
            self.cache.current_filters,
            "filters-a",
        )
        self.assertEqual(
            self.cache.version,
            1,
        )


if __name__ == "__main__":
    unittest.main()
