from math import isnan


class ChartFormatter:
    """
    Formatter dùng chung cho toàn bộ Dashboard.

    Không phụ thuộc matplotlib.
    """

    PCS = "PCS"
    HOUR = "Hour"
    MINUTE = "Minute"
    SECOND = "Second"
    PERCENT = "%"

    # ==========================================================
    # Number
    # ==========================================================

    @staticmethod
    def format_number(
        value,
        decimals=2,
    ):
        value = ChartFormatter.to_float(value)

        return f"{value:,.{decimals}f}"

    @staticmethod
    def format_integer(
        value,
    ):
        return f"{int(ChartFormatter.to_float(value)):,}"

    # ==========================================================
    # PCS
    # ==========================================================

    @classmethod
    def format_qty(
        cls,
        value,
    ):
        return (
            cls.format_integer(value)
            + " "
            + cls.PCS
        )

    # ==========================================================
    # Percent
    # ==========================================================

    @classmethod
    def format_percent(
        cls,
        value,
        decimals=2,
    ):
        return (
            cls.format_number(
                value,
                decimals,
            )
            + cls.PERCENT
        )

    # ==========================================================
    # Hour
    # ==========================================================

    @classmethod
    def format_hour(
        cls,
        value,
    ):
        value = cls.to_float(value)

        return f"{value:.2f} h"

    # ==========================================================
    # Minute
    # ==========================================================

    @classmethod
    def format_minute(
        cls,
        value,
    ):
        value = cls.to_float(value)

        return f"{value:.1f} min"

    # ==========================================================
    # Second
    # ==========================================================

    @classmethod
    def format_second(
        cls,
        value,
    ):
        value = int(cls.to_float(value))

        return f"{value} s"

    # ==========================================================
    # Runtime
    # ==========================================================

    @classmethod
    def format_runtime(
        cls,
        seconds,
    ):
        seconds = int(
            cls.to_float(seconds)
        )

        hours = seconds // 3600

        minutes = (
            seconds % 3600
        ) // 60

        sec = seconds % 60

        result = []

        if hours:
            result.append(
                f"{hours}h"
            )

        if minutes:
            result.append(
                f"{minutes}m"
            )

        if sec or not result:
            result.append(
                f"{sec}s"
            )

        return " ".join(result)

    # ==========================================================
    # Compact
    # ==========================================================

    @classmethod
    def format_compact(
        cls,
        value,
    ):
        value = cls.to_float(value)

        abs_value = abs(value)

        if abs_value >= 1_000_000_000:
            return f"{value/1_000_000_000:.2f}B"

        if abs_value >= 1_000_000:
            return f"{value/1_000_000:.2f}M"

        if abs_value >= 1_000:
            return f"{value/1_000:.2f}K"

        return cls.format_number(
            value,
            0,
        )

    # ==========================================================
    # Auto
    # ==========================================================

    @classmethod
    def auto(
        cls,
        value,
        unit="",
    ):
        unit = (
            str(unit)
            .strip()
            .lower()
        )

        if unit in (
            "%",
            "percent",
        ):
            return cls.format_percent(
                value
            )

        if unit in (
            "pcs",
            "qty",
        ):
            return cls.format_qty(
                value
            )

        if unit in (
            "hour",
            "hours",
            "h",
        ):
            return cls.format_hour(
                value
            )

        if unit in (
            "minute",
            "min",
        ):
            return cls.format_minute(
                value
            )

        if unit in (
            "second",
            "sec",
            "s",
        ):
            return cls.format_second(
                value
            )

        return cls.format_number(
            value
        )

    # ==========================================================
    # Helper
    # ==========================================================

    @staticmethod
    def to_float(value):
        try:

            value = float(value)

            if isnan(value):
                return 0.0

            return value

        except Exception:
            return 0.0