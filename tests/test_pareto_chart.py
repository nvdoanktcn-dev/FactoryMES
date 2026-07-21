from __future__ import annotations

import os
from typing import Any

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication

from src.ui.widgets.pareto_chart import (
    ParetoChart,
    ParetoItem,
)


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


def assert_close(
    actual: float,
    expected: float,
    message: str,
    tolerance: float = 0.01,
) -> None:
    if abs(actual - expected) > tolerance:
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


def get_application() -> QApplication:
    application = QApplication.instance()

    if application is None:
        application = QApplication([])

    return application


def test_set_data_sorts_and_calculates_cumulative_percent() -> None:
    get_application()

    chart = ParetoChart(
        "Pareto Downtime"
    )

    try:
        chart.set_data(
            [
                ("Mất điện", 20),
                ("Chờ liệu", 120),
                ("Sửa máy", 80),
                ("Chờ người", 40),
            ]
        )

        points = chart.points

        assert_equal(
            [point.label for point in points],
            [
                "Chờ liệu",
                "Sửa máy",
                "Chờ người",
                "Mất điện",
            ],
            "Pareto items were not sorted descending.",
        )

        assert_equal(
            [point.value for point in points],
            [
                120.0,
                80.0,
                40.0,
                20.0,
            ],
            "Pareto values are incorrect.",
        )

        assert_close(
            points[0].cumulative_percent,
            46.15,
            "First cumulative percentage is incorrect.",
        )
        assert_close(
            points[1].cumulative_percent,
            76.92,
            "Second cumulative percentage is incorrect.",
        )
        assert_close(
            points[-1].cumulative_percent,
            100.0,
            "Final cumulative percentage must be 100%.",
        )

        assert_equal(
            chart.total_label.text(),
            "Tổng: 260",
            "Total summary label is incorrect.",
        )
        assert_equal(
            chart.focus_label.text(),
            "Nhóm 80%: 3",
            "80-percent focus count is incorrect.",
        )

    finally:
        chart.close()
        chart.deleteLater()


def test_duplicate_labels_are_grouped() -> None:
    get_application()

    chart = ParetoChart()

    try:
        chart.set_data(
            [
                ("Chờ liệu", 20),
                ("Chờ liệu", 30),
                {
                    "reason": "Sửa máy",
                    "count": 40,
                },
                ParetoItem(
                    label="Mất điện",
                    value=10,
                ),
            ]
        )

        points = chart.points

        assert_equal(
            len(points),
            3,
            "Duplicate labels were not grouped.",
        )
        assert_equal(
            points[0].label,
            "Chờ liệu",
            "Grouped label order is incorrect.",
        )
        assert_equal(
            points[0].value,
            50.0,
            "Grouped value is incorrect.",
        )
        assert_close(
            points[-1].cumulative_percent,
            100.0,
            "Grouped Pareto total percentage is incorrect.",
        )

    finally:
        chart.close()
        chart.deleteLater()


def test_maximum_items_groups_remaining_values_as_other() -> None:
    get_application()

    chart = ParetoChart()

    try:
        chart.set_data(
            [
                ("A", 100),
                ("B", 80),
                ("C", 60),
                ("D", 40),
                ("E", 20),
            ],
            maximum_items=3,
        )

        points = chart.points

        assert_equal(
            len(points),
            3,
            "maximum_items did not limit the result.",
        )
        assert_equal(
            [point.label for point in points],
            [
                "A",
                "B",
                "Khác",
            ],
            "Remaining values were not grouped as Khác.",
        )
        assert_equal(
            points[2].value,
            120.0,
            "Khác value is incorrect.",
        )
        assert_close(
            points[2].cumulative_percent,
            100.0,
            "Khác cumulative percentage is incorrect.",
        )

    finally:
        chart.close()
        chart.deleteLater()


def test_dictionary_aliases_are_supported() -> None:
    get_application()

    chart = ParetoChart()

    try:
        chart.set_data(
            [
                {
                    "label": "A",
                    "value": 10,
                },
                {
                    "name": "B",
                    "frequency": 20,
                },
                {
                    "category": "C",
                    "quantity": 30,
                },
            ]
        )

        assert_equal(
            [point.label for point in chart.points],
            [
                "C",
                "B",
                "A",
            ],
            "Dictionary aliases were not normalized correctly.",
        )

    finally:
        chart.close()
        chart.deleteLater()


def test_clear_resets_points_and_summary() -> None:
    get_application()

    chart = ParetoChart()

    try:
        chart.set_data(
            [
                ("A", 10),
                ("B", 5),
            ]
        )

        chart.clear()

        assert_equal(
            chart.points,
            (),
            "clear() did not remove Pareto points.",
        )
        assert_equal(
            chart.total_label.text(),
            "Tổng: 0",
            "Total label was not reset.",
        )
        assert_equal(
            chart.focus_label.text(),
            "Nhóm 80%: 0",
            "Focus label was not reset.",
        )

    finally:
        chart.close()
        chart.deleteLater()


def test_invalid_input_is_rejected() -> None:
    get_application()

    chart = ParetoChart()

    try:
        invalid_cases = [
            (
                [
                    ParetoItem(
                        label="",
                        value=10,
                    )
                ],
                ValueError,
            ),
            (
                [
                    ParetoItem(
                        label="A",
                        value=-1,
                    )
                ],
                ValueError,
            ),
            (
                [("A", 1, 2)],
                ValueError,
            ),
            (
                [
                    {
                        "label": "A",
                    }
                ],
                ValueError,
            ),
            (
                [object()],
                TypeError,
            ),
        ]

        for items, expected_error in invalid_cases:
            try:
                chart.set_data(
                    items  # type: ignore[arg-type]
                )
            except expected_error:
                continue

            raise AssertionError(
                (
                    "Invalid Pareto input did not raise "
                    f"{expected_error.__name__}."
                )
            )

        try:
            chart.set_data(
                [("A", 1)],
                maximum_items=0,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                (
                    "maximum_items=0 must raise "
                    "ValueError."
                )
            )

    finally:
        chart.close()
        chart.deleteLater()


def test_zero_total_data_is_supported() -> None:
    get_application()

    chart = ParetoChart()

    try:
        chart.set_data(
            [
                ("A", 0),
                ("B", 0),
            ]
        )

        points = chart.points

        assert_equal(
            len(points),
            2,
            "Zero-value items were unexpectedly removed.",
        )
        assert_true(
            all(
                point.cumulative_percent == 0.0
                for point in points
            ),
            (
                "Zero-total Pareto data must have "
                "0% cumulative values."
            ),
        )
        assert_equal(
            chart.total_label.text(),
            "Tổng: 0",
            "Zero-total summary is incorrect.",
        )

    finally:
        chart.close()
        chart.deleteLater()


def run_all_tests() -> None:
    tests = [
        test_set_data_sorts_and_calculates_cumulative_percent,
        test_duplicate_labels_are_grouped,
        test_maximum_items_groups_remaining_values_as_other,
        test_dictionary_aliases_are_supported,
        test_clear_resets_points_and_summary,
        test_invalid_input_is_rejected,
        test_zero_total_data_is_supported,
    ]

    for test in tests:
        test()
        print(
            f"[PASS] {test.__name__}"
        )

    print(
        "\nAll Pareto Chart tests passed."
    )


if __name__ == "__main__":
    run_all_tests()
