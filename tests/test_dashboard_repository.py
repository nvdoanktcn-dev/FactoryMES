from __future__ import annotations

import unittest
from unittest.mock import Mock

from src.repository.dashboard_repository import (
    DashboardRepository,
)


class TestDashboardRepository(
    unittest.TestCase,
):
    def test_loader_is_required(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            DashboardRepository(
                None  # type: ignore[arg-type]
            )

    def test_loader_must_have_load_dashboard(
        self,
    ) -> None:
        with self.assertRaises(TypeError):
            DashboardRepository(
                object()  # type: ignore[arg-type]
            )

    def test_load_calls_loader(
        self,
    ) -> None:
        filters = object()
        expected = object()

        loader = Mock()
        loader.load_dashboard.return_value = (
            expected
        )

        repository = DashboardRepository(
            loader
        )

        result = repository.load(
            filters
        )

        self.assertIs(
            result,
            expected,
        )

        loader.load_dashboard.assert_called_once_with(
            filters
        )

    def test_refresh_calls_loader(
        self,
    ) -> None:
        filters = object()
        expected = object()

        loader = Mock()
        loader.load_dashboard.return_value = (
            expected
        )

        repository = DashboardRepository(
            loader
        )

        result = repository.refresh(
            filters
        )

        self.assertIs(
            result,
            expected,
        )

        loader.load_dashboard.assert_called_once_with(
            filters
        )

    def test_loader_property(
        self,
    ) -> None:
        loader = Mock()

        repository = DashboardRepository(
            loader
        )

        self.assertIs(
            repository.loader,
            loader,
        )


if __name__ == "__main__":
    unittest.main()