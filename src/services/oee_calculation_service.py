from __future__ import annotations

from math import isfinite

from src.dto.oee_result import OEEResult


class OEECalculationService:
    """
    Pure calculation service for OEE.

    All ratio results are returned as decimal values:
    0.875 means 87.5%.
    """

    @classmethod
    def calculate_availability(
        cls,
        runtime_minutes,
        downtime_minutes,
    ):
        runtime = cls._normalize_non_negative_float(
            runtime_minutes,
            "Runtime Minutes",
        )
        downtime = cls._normalize_non_negative_float(
            downtime_minutes,
            "Downtime Minutes",
        )

        planned_time = runtime + downtime

        if planned_time == 0:
            return 0.0

        return runtime / planned_time

    @classmethod
    def calculate_performance(
        cls,
        runtime_minutes,
        total_qty,
        ideal_cycle_time_sec,
    ):
        runtime = cls._normalize_non_negative_float(
            runtime_minutes,
            "Runtime Minutes",
        )
        quantity = cls._normalize_non_negative_int(
            total_qty,
            "Total Qty",
        )
        cycle_time_sec = cls._normalize_positive_float(
            ideal_cycle_time_sec,
            "Ideal Cycle Time Sec",
        )

        if runtime == 0 or quantity == 0:
            return 0.0

        ideal_production_minutes = (
            cycle_time_sec * quantity
        ) / 60.0

        return ideal_production_minutes / runtime

    @classmethod
    def calculate_quality(
        cls,
        ok_qty,
        ng_qty,
    ):
        ok = cls._normalize_non_negative_int(
            ok_qty,
            "OK Qty",
        )
        ng = cls._normalize_non_negative_int(
            ng_qty,
            "NG Qty",
        )

        total_qty = ok + ng

        if total_qty == 0:
            return 0.0

        return ok / total_qty

    @classmethod
    def calculate_oee(
        cls,
        availability,
        performance,
        quality,
    ):
        normalized_availability = (
            cls._normalize_non_negative_float(
                availability,
                "Availability",
            )
        )
        normalized_performance = (
            cls._normalize_non_negative_float(
                performance,
                "Performance",
            )
        )
        normalized_quality = (
            cls._normalize_non_negative_float(
                quality,
                "Quality",
            )
        )

        if normalized_availability > 1:
            raise ValueError(
                "Availability cannot be greater than 1."
            )

        if normalized_quality > 1:
            raise ValueError(
                "Quality cannot be greater than 1."
            )

        return (
            normalized_availability
            * normalized_performance
            * normalized_quality
        )

    @classmethod
    def calculate_execution_oee(
        cls,
        *,
        runtime_minutes,
        downtime_minutes,
        ok_qty,
        ng_qty,
        ideal_cycle_time_sec,
    ):
        runtime = cls._normalize_non_negative_float(
            runtime_minutes,
            "Runtime Minutes",
        )
        downtime = cls._normalize_non_negative_float(
            downtime_minutes,
            "Downtime Minutes",
        )
        ok = cls._normalize_non_negative_int(
            ok_qty,
            "OK Qty",
        )
        ng = cls._normalize_non_negative_int(
            ng_qty,
            "NG Qty",
        )
        cycle_time_sec = cls._normalize_positive_float(
            ideal_cycle_time_sec,
            "Ideal Cycle Time Sec",
        )

        total_qty = ok + ng

        availability = cls.calculate_availability(
            runtime,
            downtime,
        )
        performance = cls.calculate_performance(
            runtime,
            total_qty,
            cycle_time_sec,
        )
        quality = cls.calculate_quality(
            ok,
            ng,
        )
        oee = cls.calculate_oee(
            availability,
            performance,
            quality,
        )

        return OEEResult(
            availability=availability,
            performance=performance,
            quality=quality,
            oee=oee,
            runtime_minutes=runtime,
            downtime_minutes=downtime,
            total_qty=total_qty,
            ok_qty=ok,
            ng_qty=ng,
        )

    @staticmethod
    def _normalize_non_negative_float(
        value,
        field_name,
    ):
        try:
            number = float(value or 0)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid {field_name}: {value}"
            ) from error

        if not isfinite(number):
            raise ValueError(
                f"Invalid {field_name}: {value}"
            )

        if number < 0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )

        return number

    @staticmethod
    def _normalize_positive_float(
        value,
        field_name,
    ):
        try:
            number = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid {field_name}: {value}"
            ) from error

        if not isfinite(number):
            raise ValueError(
                f"Invalid {field_name}: {value}"
            )

        if number <= 0:
            raise ValueError(
                f"{field_name} must be greater than zero."
            )

        return number

    @staticmethod
    def _normalize_non_negative_int(
        value,
        field_name,
    ):
        try:
            raw_number = float(value or 0)
            if not isfinite(raw_number):
                raise ValueError
            number = int(raw_number)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(
                f"Invalid {field_name}: {value}"
            ) from error

        if number < 0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )

        return number
