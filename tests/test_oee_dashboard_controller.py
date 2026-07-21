from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from src.ui.controllers.oee_dashboard_controller import (
    OEEDashboardController,
    OEEDashboardFilters,
)


class FakeSession:
    def __init__(self) -> None:
        self.rollback_count = 0
        self.close_count = 0

    def rollback(self) -> None:
        self.rollback_count += 1

    def close(self) -> None:
        self.close_count += 1


@dataclass(slots=True)
class FakeSummary:
    execution_count: int
    planned_minutes: float
    runtime_minutes: float
    downtime_minutes: float
    ideal_runtime_minutes: float
    ok_quantity: int
    processing_ng_quantity: int
    blank_ng_quantity: int
    ng_quantity: int
    total_quantity: int
    availability: float
    performance: float
    quality: float
    oee: float


@dataclass(slots=True)
class FakeGroup:
    group_key: str
    group_label: str
    summary: FakeSummary


class FakeOEECalculationService:
    def __init__(
        self,
        session: FakeSession,
    ) -> None:
        self.session = session

    def calculate_summary(
        self,
        **kwargs: Any,
    ) -> FakeSummary:
        start_at = kwargs["start_at"]
        day = start_at.day

        if day == 2:
            return FakeSummary(
                execution_count=0,
                planned_minutes=0,
                runtime_minutes=0,
                downtime_minutes=0,
                ideal_runtime_minutes=0,
                ok_quantity=0,
                processing_ng_quantity=0,
                blank_ng_quantity=0,
                ng_quantity=0,
                total_quantity=0,
                availability=0,
                performance=0,
                quality=0,
                oee=0,
            )

        return FakeSummary(
            execution_count=2,
            planned_minutes=160,
            runtime_minutes=135,
            downtime_minutes=25,
            ideal_runtime_minutes=135,
            ok_quantity=138,
            processing_ng_quantity=12,
            blank_ng_quantity=0,
            ng_quantity=12,
            total_quantity=150,
            availability=84.38,
            performance=100.0,
            quality=92.0,
            oee=77.62,
        )

    def calculate_by_machine(
        self,
        **kwargs: Any,
    ) -> list[FakeGroup]:
        del kwargs
        return [
            FakeGroup(
                group_key="BL01",
                group_label="BL01",
                summary=self.calculate_summary(
                    start_at=type(
                        "DateValue",
                        (),
                        {"day": 1},
                    )()
                ),
            )
        ]

    def calculate_by_employee(
        self,
        **kwargs: Any,
    ) -> list[FakeGroup]:
        del kwargs
        return []

    def calculate_by_work_order(
        self,
        **kwargs: Any,
    ) -> list[FakeGroup]:
        del kwargs
        return []

    def calculate_by_product(
        self,
        **kwargs: Any,
    ) -> list[FakeGroup]:
        del kwargs
        return []

    def calculate_by_operation(
        self,
        **kwargs: Any,
    ) -> list[FakeGroup]:
        del kwargs
        return []


def assert_equal(
    actual: Any,
    expected: Any,
    message: str,
) -> None:
    if actual != expected:
        raise AssertionError(
            (
                f"{message}\n"
                f"Expected: {expected!r}\n"
                f"Actual:   {actual!r}"
            )
        )


def assert_true(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def test_filter_normalization() -> None:
    filters = OEEDashboardFilters(
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 3),
        machine_code=" BL01 ",
        employee_code="",
        shift="Tất cả",
        work_order_no=" WO-001 ",
        product_code=" P-001 ",
        operation_no="OP3",
    )

    kwargs = filters.to_service_kwargs()

    assert_equal(
        kwargs["machine_code"],
        "BL01",
        "Machine code normalization failed.",
    )
    assert_true(
        "employee_code" not in kwargs,
        "Empty employee code must be removed.",
    )
    assert_true(
        "shift" not in kwargs,
        "All-shift filter must be removed.",
    )
    assert_equal(
        kwargs["work_order_no"],
        "WO-001",
        "Work Order normalization failed.",
    )
    assert_equal(
        kwargs["product_code"],
        "P-001",
        "Product code normalization failed.",
    )
    assert_equal(
        kwargs["operation_no"],
        3,
        "Operation normalization failed.",
    )


def test_load_dashboard_and_daily_trend() -> None:
    session = FakeSession()

    controller = OEEDashboardController(
        session_factory=lambda: session,
        service_class=FakeOEECalculationService,
    )

    data = controller.load_dashboard(
        OEEDashboardFilters(
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 3),
        )
    )

    assert_equal(
        data.summary["execution_count"],
        2,
        "Summary execution count is incorrect.",
    )
    assert_equal(
        data.summary["oee"],
        77.62,
        "Summary OEE is incorrect.",
    )

    assert_equal(
        len(data.trend),
        3,
        "Trend must include every day in the range.",
    )
    assert_equal(
        data.trend[0]["label"],
        "01/07",
        "First trend label is incorrect.",
    )
    assert_equal(
        data.trend[1]["execution_count"],
        0,
        "Day without execution must remain in trend.",
    )
    assert_equal(
        data.trend[1]["oee"],
        0.0,
        "Day without execution must have zero OEE.",
    )
    assert_equal(
        data.trend[2]["oee"],
        77.62,
        "Third trend OEE is incorrect.",
    )

    assert_equal(
        len(data.by_machine),
        1,
        "Machine breakdown is incorrect.",
    )
    assert_equal(
        data.by_machine[0]["group_key"],
        "BL01",
        "Machine group key is incorrect.",
    )

    assert_equal(
        session.rollback_count,
        1,
        "Controller must rollback read-only session once.",
    )
    assert_equal(
        session.close_count,
        1,
        "Controller must close session once.",
    )


def test_invalid_date_range() -> None:
    controller = OEEDashboardController(
        session_factory=FakeSession,
        service_class=FakeOEECalculationService,
    )

    try:
        controller.load_trend(
            OEEDashboardFilters(
                start_date=date(2026, 7, 3),
                end_date=date(2026, 7, 1),
            )
        )
    except ValueError:
        return

    raise AssertionError(
        "Invalid date range must raise ValueError."
    )


def run_all_tests() -> None:
    tests = [
        test_filter_normalization,
        test_load_dashboard_and_daily_trend,
        test_invalid_date_range,
    ]

    for test in tests:
        test()
        print(
            f"[PASS] {test.__name__}"
        )

    print(
        "\nAll OEE Dashboard Controller tests passed."
    )


if __name__ == "__main__":
    run_all_tests()
