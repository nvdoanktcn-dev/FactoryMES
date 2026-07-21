from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable

from src.services.oee_pareto_service import (
    OEEParetoService,
    ParetoFilter,
    ParetoResult,
)


def assert_equal(
    actual: Any,
    expected: Any,
    message: str,
) -> None:
    if actual != expected:
        raise AssertionError(
            f"{message}\nExpected: {expected!r}\nActual:   {actual!r}"
        )


def assert_close(
    actual: float,
    expected: float,
    message: str,
    tolerance: float = 0.01,
) -> None:
    if abs(actual - expected) > tolerance:
        raise AssertionError(
            f"{message}\nExpected: {expected!r}\nActual:   {actual!r}"
        )


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises(
    expected_exception: type[BaseException],
    action: Callable[[], object],
    message: str,
) -> None:
    try:
        action()
    except expected_exception:
        return
    except Exception as error:
        raise AssertionError(
            f"{message}\nExpected: {expected_exception.__name__}\n"
            f"Actual:   {type(error).__name__}: {error}"
        ) from error

    raise AssertionError(
        f"{message}\nExpected exception: {expected_exception.__name__}"
    )


@dataclass
class DowntimeRecord:
    reason: str | None
    duration_minutes: object
    production_date: date | datetime | str | None = None
    machine_code: object | None = None
    employee_code: object | None = None
    work_order_code: object | None = None
    product_code: object | None = None


@dataclass
class NGRecord:
    ng_reason: str | None
    ng_quantity: object
    production_date: date | datetime | str | None = None
    machine_code: object | None = None
    employee_code: object | None = None
    work_order_code: object | None = None
    product_code: object | None = None


@dataclass
class CodeObject:
    code: str


def test_build_downtime_pareto_aggregates_and_sorts() -> None:
    service = OEEParetoService()
    result = service.build_downtime_pareto(
        [
            DowntimeRecord("Chờ liệu", 40),
            DowntimeRecord("Sửa máy", 75),
            DowntimeRecord("Chờ liệu", 80),
            DowntimeRecord("Mất điện", 20),
        ]
    )

    assert_equal(
        [item.label for item in result.items],
        ["Chờ liệu", "Sửa máy", "Mất điện"],
        "Downtime labels were not grouped and sorted correctly.",
    )
    assert_equal(
        [item.value for item in result.items],
        [120.0, 75.0, 20.0],
        "Downtime values are incorrect.",
    )
    assert_close(result.total_value, 215.0, "Downtime total is incorrect.")
    assert_close(
        result.items[0].cumulative_percent,
        55.81,
        "First downtime cumulative percentage is incorrect.",
    )
    assert_close(
        result.items[-1].cumulative_percent,
        100.0,
        "Final downtime cumulative percentage must be 100%.",
    )
    assert_equal(result.focus_item_count, 2, "80% focus count is incorrect.")
    assert_equal(result.source_record_count, 4, "Source count is incorrect.")
    assert_equal(result.ignored_record_count, 0, "Ignored count is incorrect.")


def test_build_ng_pareto_supports_alias_fields() -> None:
    service = OEEParetoService()
    result = service.build_ng_pareto(
        [
            {"defect_reason": "Gia công", "defect_quantity": 7},
            {"ng_reason": "Phôi", "ng_quantity": 4},
            {"reason": "Gia công", "quantity": 3},
            NGRecord("Khác", Decimal("2")),
        ]
    )

    assert_equal(
        [item.label for item in result.items],
        ["Gia công", "Phôi", "Khác"],
        "NG labels were not aggregated correctly.",
    )
    assert_equal(
        [item.value for item in result.items],
        [10.0, 4.0, 2.0],
        "NG values are incorrect.",
    )
    assert_close(result.total_value, 16.0, "NG total is incorrect.")
    assert_equal(result.focus_item_count, 2, "NG focus count is incorrect.")


def test_generic_pareto_supports_custom_fields() -> None:
    service = OEEParetoService()
    result = service.build_generic_pareto(
        [
            {"category_name": "A", "minutes_lost": 15},
            {"category_name": "B", "minutes_lost": 10},
            {"category_name": "A", "minutes_lost": 5},
        ],
        label_fields=("category_name",),
        value_fields=("minutes_lost",),
    )

    assert_equal(
        [(item.label, item.value) for item in result.items],
        [("A", 20.0), ("B", 10.0)],
        "Custom field aggregation is incorrect.",
    )


def test_filters_by_date_machine_employee_work_order_and_product() -> None:
    service = OEEParetoService()
    records = [
        DowntimeRecord(
            "Chờ liệu",
            30,
            production_date=date(2026, 7, 1),
            machine_code="BL01",
            employee_code="NV01",
            work_order_code="WO01",
            product_code="SP01",
        ),
        DowntimeRecord(
            "Sửa máy",
            50,
            production_date=datetime(2026, 7, 2, 8, 0),
            machine_code={"code": "BL02"},
            employee_code=CodeObject("NV02"),
            work_order_code="WO02",
            product_code="SP02",
        ),
        DowntimeRecord(
            "Mất điện",
            70,
            production_date="2026-07-03",
            machine_code="BL02",
            employee_code="NV02",
            work_order_code="WO02",
            product_code="SP02",
        ),
    ]

    result = service.build_downtime_pareto(
        records,
        filters=ParetoFilter(
            start_date=date(2026, 7, 2),
            end_date=date(2026, 7, 2),
            machine_codes=(" bl02 ",),
            employee_codes=("NV02",),
            work_order_codes=("wo02",),
            product_codes=("SP02",),
        ),
    )

    assert_equal(len(result.items), 1, "Combined filters returned wrong item count.")
    assert_equal(result.items[0].label, "Sửa máy", "Combined filters selected wrong record.")
    assert_equal(result.items[0].value, 50.0, "Filtered value is incorrect.")
    assert_equal(result.source_record_count, 3, "Filtered source count is incorrect.")
    assert_equal(result.ignored_record_count, 2, "Filtered ignored count is incorrect.")


def test_date_filter_rejects_records_without_valid_date() -> None:
    service = OEEParetoService()
    result = service.build_downtime_pareto(
        [
            DowntimeRecord("A", 10, production_date=None),
            DowntimeRecord("B", 20, production_date="invalid"),
            DowntimeRecord("C", 30, production_date="2026-07-10T08:30:00"),
        ],
        filters=ParetoFilter(start_date=date(2026, 7, 10)),
    )

    assert_equal(
        [(item.label, item.value) for item in result.items],
        [("C", 30.0)],
        "Date filter did not ignore missing or invalid dates.",
    )
    assert_equal(result.ignored_record_count, 2, "Date filter ignored count is incorrect.")


def test_maximum_items_groups_remaining_as_other() -> None:
    service = OEEParetoService()
    result = service.build_downtime_pareto(
        [
            DowntimeRecord("A", 100),
            DowntimeRecord("B", 80),
            DowntimeRecord("C", 60),
            DowntimeRecord("D", 40),
            DowntimeRecord("E", 20),
        ],
        maximum_items=3,
    )

    assert_equal(
        [(item.label, item.value) for item in result.items],
        [("A", 100.0), ("B", 80.0), ("Khác", 120.0)],
        "maximum_items grouping is incorrect.",
    )
    assert_close(result.total_value, 300.0, "Grouped total must be preserved.")
    assert_close(result.items[-1].cumulative_percent, 100.0, "Grouped cumulative percent is incorrect.")


def test_maximum_items_one_groups_everything_as_other() -> None:
    service = OEEParetoService()
    result = service.build_ng_pareto(
        [NGRecord("A", 5), NGRecord("B", 3), NGRecord("C", 2)],
        maximum_items=1,
    )

    assert_equal(len(result.items), 1, "maximum_items=1 must return one item.")
    assert_equal(result.items[0].label, "Khác", "Single grouped label must be Khác.")
    assert_equal(result.items[0].value, 10.0, "Single grouped value is incorrect.")


def test_focus_threshold_changes_focus_item_count() -> None:
    service = OEEParetoService()
    records = [
        DowntimeRecord("A", 50),
        DowntimeRecord("B", 30),
        DowntimeRecord("C", 20),
    ]

    result_50 = service.build_downtime_pareto(records, focus_threshold=50)
    result_90 = service.build_downtime_pareto(records, focus_threshold=90)

    assert_equal(result_50.focus_item_count, 1, "50% focus count is incorrect.")
    assert_equal(result_90.focus_item_count, 3, "90% focus count is incorrect.")
    assert_equal(result_90.focus_threshold, 90.0, "Focus threshold was not preserved.")


def test_invalid_and_zero_values_are_ignored_by_default() -> None:
    service = OEEParetoService()
    result = service.build_downtime_pareto(
        [
            DowntimeRecord("Valid", 10),
            DowntimeRecord("Missing", None),
            DowntimeRecord("Negative", -5),
            DowntimeRecord("Text", "abc"),
            DowntimeRecord("Boolean", True),
            DowntimeRecord("NaN", float("nan")),
            DowntimeRecord("Infinity", float("inf")),
            DowntimeRecord("Zero", 0),
        ]
    )

    assert_equal(
        [(item.label, item.value) for item in result.items],
        [("Valid", 10.0)],
        "Invalid values were not ignored correctly.",
    )
    assert_equal(result.source_record_count, 8, "Invalid-data source count is incorrect.")
    assert_equal(result.ignored_record_count, 7, "Invalid-data ignored count is incorrect.")


def test_include_zero_and_unknown_label() -> None:
    service = OEEParetoService()
    result = service.build_downtime_pareto(
        [
            DowntimeRecord(None, 0),
            DowntimeRecord("", 5),
            DowntimeRecord("A", 5),
        ],
        include_zero=True,
        unknown_label="Chưa khai báo",
    )

    assert_equal(
        [(item.label, item.value) for item in result.items],
        [("A", 5.0), ("Chưa khai báo", 5.0)],
        "Zero inclusion or unknown-label grouping is incorrect.",
    )
    assert_equal(result.ignored_record_count, 0, "Zero values should not be ignored.")


def test_empty_result_is_valid() -> None:
    service = OEEParetoService()
    result = service.build_ng_pareto([])

    assert_equal(result.items, (), "Empty input must produce no items.")
    assert_equal(result.total_value, 0.0, "Empty total must be zero.")
    assert_equal(result.focus_item_count, 0, "Empty focus count must be zero.")
    assert_equal(result.source_record_count, 0, "Empty source count must be zero.")
    assert_equal(result.ignored_record_count, 0, "Empty ignored count must be zero.")


def test_to_chart_items_returns_chart_compatible_dicts() -> None:
    service = OEEParetoService()
    result = service.build_downtime_pareto(
        [DowntimeRecord("A", 20), DowntimeRecord("B", 10)]
    )

    chart_items = service.to_chart_items(result)

    assert_equal(
        chart_items,
        [
            {"label": "A", "value": 20.0},
            {"label": "B", "value": 10.0},
        ],
        "Chart-item conversion is incorrect.",
    )


def test_result_to_dict_contains_serializable_structure() -> None:
    service = OEEParetoService()
    result = service.build_ng_pareto([NGRecord("Gia công", 4)])
    payload = result.to_dict()

    assert_equal(payload["total_value"], 4.0, "Result dictionary total is incorrect.")
    assert_equal(payload["focus_item_count"], 1, "Result dictionary focus count is incorrect.")
    assert_equal(
        payload["items"],
        [
            {
                "label": "Gia công",
                "value": 4.0,
                "cumulative_value": 4.0,
                "cumulative_percent": 100.0,
                "rank": 1,
            }
        ],
        "Result dictionary items are incorrect.",
    )


def test_validation_errors() -> None:
    service = OEEParetoService()

    assert_raises(
        ValueError,
        lambda: service.build_generic_pareto([], label_fields=(), value_fields=("value",)),
        "Empty label_fields must fail.",
    )
    assert_raises(
        ValueError,
        lambda: service.build_generic_pareto([], label_fields=("label",), value_fields=()),
        "Empty value_fields must fail.",
    )
    assert_raises(
        ValueError,
        lambda: service.build_downtime_pareto([], maximum_items=0),
        "maximum_items below one must fail.",
    )
    assert_raises(
        ValueError,
        lambda: service.build_downtime_pareto([], focus_threshold=0),
        "Zero focus threshold must fail.",
    )
    assert_raises(
        ValueError,
        lambda: service.build_downtime_pareto([], focus_threshold=101),
        "Focus threshold above 100 must fail.",
    )
    assert_raises(
        ValueError,
        lambda: ParetoFilter(
            start_date=date(2026, 7, 2),
            end_date=date(2026, 7, 1),
        ).normalized(),
        "Reversed date range must fail.",
    )
    assert_raises(
        TypeError,
        lambda: ParetoFilter(start_date="2026-07-01").normalized(),  # type: ignore[arg-type]
        "Invalid filter date type must fail.",
    )
    assert_raises(
        TypeError,
        lambda: service.to_chart_items(object()),  # type: ignore[arg-type]
        "to_chart_items must reject non-ParetoResult input.",
    )


def test_alphabetical_tie_break_and_ranks() -> None:
    service = OEEParetoService()
    result = service.build_downtime_pareto(
        [
            DowntimeRecord("Beta", 10),
            DowntimeRecord("alpha", 10),
            DowntimeRecord("Gamma", 5),
        ]
    )

    assert_equal(
        [item.label for item in result.items],
        ["alpha", "Beta", "Gamma"],
        "Equal values must use case-insensitive alphabetical ordering.",
    )
    assert_equal(
        [item.rank for item in result.items],
        [1, 2, 3],
        "Pareto ranks are incorrect.",
    )


def run_all_tests() -> None:
    tests = [
        test_build_downtime_pareto_aggregates_and_sorts,
        test_build_ng_pareto_supports_alias_fields,
        test_generic_pareto_supports_custom_fields,
        test_filters_by_date_machine_employee_work_order_and_product,
        test_date_filter_rejects_records_without_valid_date,
        test_maximum_items_groups_remaining_as_other,
        test_maximum_items_one_groups_everything_as_other,
        test_focus_threshold_changes_focus_item_count,
        test_invalid_and_zero_values_are_ignored_by_default,
        test_include_zero_and_unknown_label,
        test_empty_result_is_valid,
        test_to_chart_items_returns_chart_compatible_dicts,
        test_result_to_dict_contains_serializable_structure,
        test_validation_errors,
        test_alphabetical_tie_break_and_ranks,
    ]

    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")

    print(f"\nAll {len(tests)} OEE Pareto service tests passed.")


if __name__ == "__main__":
    run_all_tests()
