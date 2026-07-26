from __future__ import annotations

import unittest
from types import SimpleNamespace

from src.providers.dashboard_data_provider import (
    DashboardDataProvider,
)


class FakeCache:
    def __init__(
        self,
        current_data=None,
    ) -> None:
        self.current_data = current_data


class TestDashboardDataProvider(
    unittest.TestCase,
):
    def test_cache_is_required(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            DashboardDataProvider(
                None  # type: ignore[arg-type]
            )

    def test_cache_must_have_current_data(
        self,
    ) -> None:
        with self.assertRaises(TypeError):
            DashboardDataProvider(
                object()  # type: ignore[arg-type]
            )

    def test_cache_property(
        self,
    ) -> None:
        cache = FakeCache()

        provider = DashboardDataProvider(
            cache
        )

        self.assertIs(
            provider.cache,
            cache,
        )

    def test_dashboard_property(
        self,
    ) -> None:
        dashboard = object()
        cache = FakeCache(
            dashboard
        )

        provider = DashboardDataProvider(
            cache
        )

        self.assertIs(
            provider.dashboard,
            dashboard,
        )

    def test_require_dashboard_raises_when_empty(
        self,
    ) -> None:
        provider = DashboardDataProvider(
            FakeCache()
        )

        with self.assertRaises(RuntimeError):
            provider.require_dashboard()

    def test_require_dashboard_returns_data(
        self,
    ) -> None:
        dashboard = object()

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertIs(
            provider.require_dashboard(),
            dashboard,
        )

    def test_kpi_data_prefers_kpi(
        self,
    ) -> None:
        kpi = object()
        summary = object()

        dashboard = SimpleNamespace(
            kpi=kpi,
            summary=summary,
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertIs(
            provider.kpi_data(),
            kpi,
        )

    def test_kpi_data_falls_back_to_summary(
        self,
    ) -> None:
        summary = object()

        dashboard = SimpleNamespace(
            kpi=None,
            summary=summary,
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertIs(
            provider.kpi_data(),
            summary,
        )

    def test_kpi_data_falls_back_to_overall(
        self,
    ) -> None:
        overall = object()

        dashboard = SimpleNamespace(
            overall=overall,
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertIs(
            provider.kpi_data(),
            overall,
        )

    def test_kpi_data_falls_back_to_dashboard(
        self,
    ) -> None:
        dashboard = SimpleNamespace()

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertIs(
            provider.kpi_data(),
            dashboard,
        )

    def test_machine_data_prefers_top_machines(
        self,
    ) -> None:
        top_machines = ["BL01"]
        by_machine = ["BL02"]

        dashboard = SimpleNamespace(
            top_machines=top_machines,
            by_machine=by_machine,
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertEqual(
            provider.machine_data(),
            ["BL01"],
        )

    def test_machine_data_falls_back_to_by_machine(
        self,
    ) -> None:
        dashboard = SimpleNamespace(
            by_machine=("BL01", "BL02")
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertEqual(
            provider.machine_data(),
            ["BL01", "BL02"],
        )

    def test_pareto_data(
        self,
    ) -> None:
        rows = [
            {"reason": "Gia công NG"}
        ]

        dashboard = SimpleNamespace(
            pareto_rows=rows
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertEqual(
            provider.pareto_data(),
            rows,
        )

    def test_trend_data(
        self,
    ) -> None:
        rows = (
            {"date": "2026-07-01"},
            {"date": "2026-07-02"},
        )

        dashboard = SimpleNamespace(
            execution_rows=rows
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertEqual(
            provider.trend_data(),
            list(rows),
        )

    def test_progress_data(
        self,
    ) -> None:
        rows = [
            {"work_order": "WO-001"}
        ]

        dashboard = SimpleNamespace(
            by_work_order=rows
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertEqual(
            provider.progress_data(),
            rows,
        )

    def test_breakdown_machine(
        self,
    ) -> None:
        rows = ["BL01"]

        dashboard = SimpleNamespace(
            by_machine=rows
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertEqual(
            provider.breakdown_data(
                "machine"
            ),
            rows,
        )

    def test_breakdown_employee(
        self,
    ) -> None:
        rows = ["NV001"]

        dashboard = SimpleNamespace(
            by_employee=rows
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertEqual(
            provider.breakdown_data(
                "employee"
            ),
            rows,
        )

    def test_breakdown_work_order(
        self,
    ) -> None:
        rows = ["WO-001"]

        dashboard = SimpleNamespace(
            by_work_order=rows
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertEqual(
            provider.breakdown_data(
                "work_order"
            ),
            rows,
        )

    def test_breakdown_product(
        self,
    ) -> None:
        rows = ["PRODUCT-A"]

        dashboard = SimpleNamespace(
            by_product=rows
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertEqual(
            provider.breakdown_data(
                "product"
            ),
            rows,
        )

    def test_breakdown_operation(
        self,
    ) -> None:
        rows = ["OP1"]

        dashboard = SimpleNamespace(
            by_operation=rows
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertEqual(
            provider.breakdown_data(
                "operation"
            ),
            rows,
        )

    def test_breakdown_name_is_normalized(
        self,
    ) -> None:
        rows = ["BL01"]

        dashboard = SimpleNamespace(
            by_machine=rows
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertEqual(
            provider.breakdown_data(
                " MACHINE "
            ),
            rows,
        )

    def test_invalid_breakdown_raises(
        self,
    ) -> None:
        provider = DashboardDataProvider(
            FakeCache(
                SimpleNamespace()
            )
        )

        with self.assertRaises(ValueError):
            provider.breakdown_data(
                "unknown"
            )

    def test_missing_sequence_returns_empty_list(
        self,
    ) -> None:
        provider = DashboardDataProvider(
            FakeCache(
                SimpleNamespace()
            )
        )

        self.assertEqual(
            provider.trend_data(),
            [],
        )

    def test_empty_list_is_valid_and_stops_fallback(
        self,
    ) -> None:
        dashboard = SimpleNamespace(
            top_machines=[],
            by_machine=["BL01"],
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertEqual(
            provider.machine_data(),
            [],
        )

    def test_mapping_dashboard_is_supported(
        self,
    ) -> None:
        dashboard = {
            "by_product": [
                "PRODUCT-A",
                "PRODUCT-B",
            ]
        }

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertEqual(
            provider.breakdown_data(
                "product"
            ),
            [
                "PRODUCT-A",
                "PRODUCT-B",
            ],
        )

    def test_mapping_is_not_treated_as_sequence(
        self,
    ) -> None:
        dashboard = SimpleNamespace(
            trend_rows={
                "date": "2026-07-01"
            }
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertEqual(
            provider.trend_data(),
            [],
        )

    def test_string_is_not_treated_as_sequence(
        self,
    ) -> None:
        dashboard = SimpleNamespace(
            progress_rows="WO-001"
        )

        provider = DashboardDataProvider(
            FakeCache(dashboard)
        )

        self.assertEqual(
            provider.progress_data(),
            [],
        )


if __name__ == "__main__":
    unittest.main()