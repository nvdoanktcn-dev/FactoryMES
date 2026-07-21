from __future__ import annotations

import math
from statistics import median


class ChartUtils:
    """
    Utility dùng chung cho toàn bộ Chart Framework.

    Không phụ thuộc PySide6.
    Không phụ thuộc matplotlib.
    """

    # ==========================================================
    # Numeric normalization
    # ==========================================================

    @staticmethod
    def to_float(
        value,
        default=0.0,
    ):
        try:
            number = float(value)

            if not math.isfinite(number):
                return float(default)

            return number

        except (
            TypeError,
            ValueError,
        ):
            return float(default)

    @classmethod
    def normalize_values(
        cls,
        values,
        default=0.0,
        allow_negative=True,
    ):
        result = []

        for value in values or []:
            number = cls.to_float(
                value,
                default=default,
            )

            if not allow_negative:
                number = max(
                    number,
                    0.0,
                )

            result.append(number)

        return result

    @staticmethod
    def normalize_labels(values):
        return [
            str(value or "").strip()
            for value in values or []
        ]

    @classmethod
    def normalize_percent(
        cls,
        value,
        minimum=0.0,
        maximum=100.0,
    ):
        number = cls.to_float(value)

        return min(
            max(number, minimum),
            maximum,
        )

    # ==========================================================
    # Basic statistics
    # ==========================================================

    @classmethod
    def total(cls, values):
        return sum(
            cls.normalize_values(values)
        )

    @classmethod
    def average(cls, values):
        numbers = cls.normalize_values(values)

        if not numbers:
            return 0.0

        return sum(numbers) / len(numbers)

    @classmethod
    def minimum(cls, values):
        numbers = cls.normalize_values(values)

        if not numbers:
            return 0.0

        return min(numbers)

    @classmethod
    def maximum(cls, values):
        numbers = cls.normalize_values(values)

        if not numbers:
            return 0.0

        return max(numbers)

    @classmethod
    def median_value(cls, values):
        numbers = cls.normalize_values(values)

        if not numbers:
            return 0.0

        return float(median(numbers))

    @classmethod
    def variance(cls, values):
        numbers = cls.normalize_values(values)

        if not numbers:
            return 0.0

        average_value = cls.average(numbers)

        return sum(
            (value - average_value) ** 2
            for value in numbers
        ) / len(numbers)

    # ==========================================================
    # Axis calculations
    # ==========================================================

    @classmethod
    def calculate_axis_max(
        cls,
        values,
        padding_ratio=0.10,
        minimum_axis_max=1.0,
    ):
        numbers = cls.normalize_values(values)

        if not numbers:
            return float(minimum_axis_max)

        maximum_value = max(numbers)

        if maximum_value <= 0:
            return float(minimum_axis_max)

        padded_value = maximum_value * (
            1.0 + max(
                cls.to_float(padding_ratio),
                0.0,
            )
        )

        step = cls.calculate_tick_step(
            padded_value
        )

        if step <= 0:
            return max(
                padded_value,
                minimum_axis_max,
            )

        rounded_max = math.ceil(
            padded_value / step
        ) * step

        return max(
            rounded_max,
            float(minimum_axis_max),
        )

    @classmethod
    def calculate_axis_min(
        cls,
        values,
        padding_ratio=0.10,
        force_zero=True,
    ):
        numbers = cls.normalize_values(values)

        if not numbers:
            return 0.0

        minimum_value = min(numbers)

        if force_zero and minimum_value >= 0:
            return 0.0

        padding = abs(minimum_value) * max(
            cls.to_float(padding_ratio),
            0.0,
        )

        return minimum_value - padding

    @classmethod
    def calculate_tick_step(
        cls,
        axis_max,
        target_tick_count=6,
    ):
        axis_max = cls.to_float(axis_max)

        if axis_max <= 0:
            return 1.0

        target_tick_count = max(
            int(target_tick_count or 6),
            2,
        )

        raw_step = axis_max / target_tick_count

        exponent = math.floor(
            math.log10(raw_step)
        )

        magnitude = 10 ** exponent
        normalized = raw_step / magnitude

        if normalized <= 1:
            nice_step = 1

        elif normalized <= 2:
            nice_step = 2

        elif normalized <= 5:
            nice_step = 5

        else:
            nice_step = 10

        return nice_step * magnitude

    # ==========================================================
    # Sorting and ranking
    # ==========================================================

    @classmethod
    def sort_pairs(
        cls,
        labels,
        values,
        reverse=False,
    ):
        normalized_labels = cls.normalize_labels(
            labels
        )

        normalized_values = cls.normalize_values(
            values
        )

        if len(normalized_labels) != len(
            normalized_values
        ):
            raise ValueError(
                "Labels and values must have "
                "the same length."
            )

        pairs = list(
            zip(
                normalized_labels,
                normalized_values,
            )
        )

        return sorted(
            pairs,
            key=lambda item: item[1],
            reverse=reverse,
        )

    @classmethod
    def top_n(
        cls,
        labels,
        values,
        limit=10,
    ):
        limit = max(
            int(limit or 0),
            0,
        )

        pairs = cls.sort_pairs(
            labels,
            values,
            reverse=True,
        )

        if limit == 0:
            return []

        return pairs[:limit]

    @classmethod
    def rank_values(
        cls,
        values,
        descending=True,
    ):
        numbers = cls.normalize_values(values)

        unique_values = sorted(
            set(numbers),
            reverse=descending,
        )

        rank_map = {
            value: rank
            for rank, value in enumerate(
                unique_values,
                start=1,
            )
        }

        return [
            rank_map[value]
            for value in numbers
        ]

    # ==========================================================
    # Percent / Pareto
    # ==========================================================

    @classmethod
    def calculate_percentages(
        cls,
        values,
    ):
        numbers = cls.normalize_values(
            values,
            allow_negative=False,
        )

        total_value = sum(numbers)

        if total_value <= 0:
            return [
                0.0
                for _ in numbers
            ]

        return [
            value / total_value * 100
            for value in numbers
        ]

    @classmethod
    def calculate_cumulative(
        cls,
        values,
    ):
        numbers = cls.normalize_values(
            values,
            allow_negative=False,
        )

        running_total = 0.0
        result = []

        for value in numbers:
            running_total += value
            result.append(running_total)

        return result

    @classmethod
    def calculate_cumulative_percent(
        cls,
        values,
    ):
        cumulative = cls.calculate_cumulative(
            values
        )

        if not cumulative:
            return []

        total_value = cumulative[-1]

        if total_value <= 0:
            return [
                0.0
                for _ in cumulative
            ]

        return [
            value / total_value * 100
            for value in cumulative
        ]

    @classmethod
    def pareto_data(
        cls,
        labels,
        values,
        limit=None,
    ):
        pairs = cls.sort_pairs(
            labels,
            values,
            reverse=True,
        )

        if limit is not None:
            limit = max(
                int(limit),
                0,
            )
            pairs = pairs[:limit]

        sorted_labels = [
            label
            for label, _ in pairs
        ]

        sorted_values = [
            value
            for _, value in pairs
        ]

        return {
            "labels": sorted_labels,
            "values": sorted_values,
            "percentages":
                cls.calculate_percentages(
                    sorted_values
                ),
            "cumulative_percent":
                cls.calculate_cumulative_percent(
                    sorted_values
                ),
        }

    # ==========================================================
    # Trend calculations
    # ==========================================================

    @classmethod
    def moving_average(
        cls,
        values,
        window_size=3,
    ):
        numbers = cls.normalize_values(values)

        window_size = int(
            window_size or 0
        )

        if window_size <= 0:
            raise ValueError(
                "Window Size must be greater "
                "than zero."
            )

        result = []

        for index in range(len(numbers)):
            start_index = max(
                0,
                index - window_size + 1,
            )

            window = numbers[
                start_index:index + 1
            ]

            result.append(
                cls.average(window)
            )

        return result

    @classmethod
    def growth_rates(
        cls,
        values,
    ):
        numbers = cls.normalize_values(values)

        if not numbers:
            return []

        result = [0.0]

        for index in range(
            1,
            len(numbers),
        ):
            previous = numbers[index - 1]
            current = numbers[index]

            if previous == 0:
                result.append(0.0)
                continue

            result.append(
                (
                    current - previous
                )
                / abs(previous)
                * 100
            )

        return result

    @classmethod
    def linear_trend(
        cls,
        values,
    ):
        numbers = cls.normalize_values(values)

        count = len(numbers)

        if count == 0:
            return []

        if count == 1:
            return [numbers[0]]

        x_values = list(range(count))

        x_average = cls.average(x_values)
        y_average = cls.average(numbers)

        numerator = sum(
            (
                x_value - x_average
            )
            * (
                y_value - y_average
            )
            for x_value, y_value
            in zip(
                x_values,
                numbers,
            )
        )

        denominator = sum(
            (
                x_value - x_average
            ) ** 2
            for x_value in x_values
        )

        slope = (
            numerator / denominator
            if denominator > 0
            else 0.0
        )

        intercept = (
            y_average
            - slope * x_average
        )

        return [
            intercept + slope * x_value
            for x_value in x_values
        ]

    # ==========================================================
    # Series helpers
    # ==========================================================

    @classmethod
    def flatten_series(
        cls,
        series_list,
    ):
        values = []

        for series in series_list or []:
            series_values = getattr(
                series,
                "values",
                [],
            )

            values.extend(
                cls.normalize_values(
                    series_values
                )
            )

        return values

    @classmethod
    def validate_series_lengths(
        cls,
        labels,
        series_list,
    ):
        label_count = len(
            labels or []
        )

        for series in series_list or []:
            series_name = str(
                getattr(
                    series,
                    "name",
                    "",
                )
                or ""
            )

            values = getattr(
                series,
                "values",
                [],
            )

            if len(values) != label_count:
                raise ValueError(
                    f"Series '{series_name}' has "
                    f"{len(values)} values, but "
                    f"labels contain {label_count} items."
                )

        return True