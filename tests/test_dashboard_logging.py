from __future__ import annotations

import unittest

from src.dashboard.dashboard_builder import DashboardBuilder
from src.dashboard.dashboard_logger import DASHBOARD_LOGGER_NAME

class FakeDashboardLoader:
    def __init__(self):
        self.calls = []
        self.result = {
            "dashboard": "data",
        }

    def load(self, filters):
        self.calls.append(filters)
        return self.result

class FailingDashboardLoader:
    def __init__(self, error=None):
        self.error = error or RuntimeError("load failed")

    def load(self, filters):
        raise self.error

class TestDashboardLogging(unittest.TestCase):
    def test_coordinator_load_writes_info_log(self):
        coordinator = DashboardBuilder.build(
            FakeDashboardLoader()
        )

        with self.assertLogs(
            DASHBOARD_LOGGER_NAME,
            level="INFO",
        ) as captured:
            coordinator.load({"month": 7})

        output = "\n".join(captured.output)

        self.assertIn(
            "Dashboard coordinator load requested",
            output,
        )
        self.assertIn(
            "Dashboard coordinator load completed",
            output,
        )

    def test_repository_load_writes_info_log(self):
        coordinator = DashboardBuilder.build(
            FakeDashboardLoader()
        )

        with self.assertLogs(
            DASHBOARD_LOGGER_NAME,
            level="INFO",
        ) as captured:
            coordinator.load({"month": 7})

        output = "\n".join(captured.output)

        self.assertIn(
            "Dashboard repository load started",
            output,
        )
        self.assertIn(
            "Dashboard repository load completed",
            output,
        )

    def test_cache_hit_writes_debug_log(self):
        coordinator = DashboardBuilder.build(
            FakeDashboardLoader()
        )
        filters = {"month": 7}

        coordinator.load(filters)

        with self.assertLogs(
            DASHBOARD_LOGGER_NAME,
            level="DEBUG",
        ) as captured:
            coordinator.load(filters)

        output = "\n".join(captured.output)

        self.assertIn(
            "Dashboard cache hit",
            output,
        )

    def test_cache_miss_writes_debug_log(self):
        coordinator = DashboardBuilder.build(
            FakeDashboardLoader()
        )

        with self.assertLogs(
            DASHBOARD_LOGGER_NAME,
            level="DEBUG",
        ) as captured:
            coordinator.load({"month": 7})

        output = "\n".join(captured.output)

        self.assertIn(
            "Dashboard cache miss",
            output,
        )

    def test_refresh_writes_logs(self):
        coordinator = DashboardBuilder.build(
            FakeDashboardLoader()
        )

        with self.assertLogs(
            DASHBOARD_LOGGER_NAME,
            level="INFO",
        ) as captured:
            coordinator.refresh({"month": 7})

        output = "\n".join(captured.output)

        self.assertIn(
            "Dashboard coordinator refresh requested",
            output,
        )
        self.assertIn(
            "Dashboard cache refresh completed",
            output,
        )
        self.assertIn(
            "Dashboard coordinator refresh completed",
            output,
        )

    def test_invalidate_writes_log(self):
        coordinator = DashboardBuilder.build(
            FakeDashboardLoader()
        )

        coordinator.load({"month": 7})

        with self.assertLogs(
            DASHBOARD_LOGGER_NAME,
            level="INFO",
        ) as captured:
            coordinator.invalidate()

        output = "\n".join(captured.output)

        self.assertIn(
            "Dashboard coordinator invalidate requested",
            output,
        )
        self.assertIn(
            "Dashboard cache invalidated",
            output,
        )
        self.assertIn(
            "Dashboard coordinator invalidate completed",
            output,
        )

    def test_failed_load_writes_error_log_and_reraises(self):
        error = RuntimeError("database unavailable")

        coordinator = DashboardBuilder.build(
            FailingDashboardLoader(error)
        )

        with self.assertLogs(
            DASHBOARD_LOGGER_NAME,
            level="ERROR",
        ) as captured:
            with self.assertRaises(RuntimeError) as context:
                coordinator.load({"month": 7})

        self.assertIs(context.exception, error)

        output = "\n".join(captured.output)

        self.assertIn(
            "Dashboard repository load failed",
            output,
        )
        self.assertIn(
            "Dashboard cache refresh failed",
            output,
        )
        self.assertIn(
            "Dashboard coordinator load failed",
            output,
        )

    def test_logging_does_not_change_returned_object(self):
        loader = FakeDashboardLoader()
        coordinator = DashboardBuilder.build(loader)

        result = coordinator.load({"month": 7})

        self.assertIs(result, loader.result)

    def test_logging_does_not_change_cache_behavior(self):
        loader = FakeDashboardLoader()
        coordinator = DashboardBuilder.build(loader)

        filters = {"month": 7}

        result_a = coordinator.load(filters)
        result_b = coordinator.load(filters)

        self.assertIs(result_a, result_b)
        self.assertEqual(len(loader.calls), 1)


if __name__ == "__main__":
    unittest.main()

class SwitchableDashboardLoader:
    def __init__(self):
        self.result = {"version": 1}
        self.error = None

    def load(self, filters):
        if self.error is not None:
            raise self.error

        return self.result

    def test_failed_refresh_preserves_previous_cache_snapshot(self):
        loader = SwitchableDashboardLoader()
        coordinator = DashboardBuilder.build(loader)

        old_filters = {"month": 6}
        old_data = coordinator.load(old_filters)
        old_version = coordinator.version
    
        loader.error = RuntimeError("temporary failure")

        with self.assertLogs(
            DASHBOARD_LOGGER_NAME,
            level="ERROR",
        ):
            with self.assertRaises(RuntimeError):
                coordinator.refresh({"month": 7})

        self.assertIs(
            coordinator.current_data,
            old_data,
        )
        self.assertEqual(
                coordinator.current_filters,
            old_filters,
        )
        self.assertEqual(
            coordinator.version,
            old_version,
        )
        self.assertTrue(
            coordinator.has_data,
        )

