from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

from src.dto.oee_result import OEEResult
from src.services.oee_calculation_service import (
    OEECalculationService,
)


@dataclass(slots=True, frozen=True)
class OEEAggregationRow:
    runtime_minutes: float
    downtime_minutes: float
    ok_qty: int
    ng_qty: int
    cycle_time_sec: float
    work_order_no: str = ""
    product_code: str = ""
    operation_no: int | None = None
    is_final_operation: bool | None = None


class OEEAggregationService:
    """
    Aggregate many execution rows into one OEEResult.

    Mixed products/operations are supported by calculating a
    quantity-weighted ideal cycle time before delegating the final
    OEE calculation to OEECalculationService.
    """

    @classmethod
    def aggregate(
        cls,
        rows: Iterable[OEEAggregationRow],
    ) -> OEEResult:
        normalized_rows = [
            cls._normalize_row(row)
            for row in rows
        ]

        if not normalized_rows:
            return cls.empty_result()

        runtime_minutes = sum(
            row.runtime_minutes
            for row in normalized_rows
        )
        downtime_minutes = sum(
            row.downtime_minutes
            for row in normalized_rows
        )
        output_rows = cls._select_output_rows(
            normalized_rows
        )
        ok_qty = sum(
            row.ok_qty
            for row in output_rows
        )
        ng_qty = sum(
            row.ng_qty
            for row in output_rows
        )
        total_qty = ok_qty + ng_qty

        if total_qty == 0:
            return OEEResult(
                availability=(
                    OEECalculationService
                    .calculate_availability(
                        runtime_minutes,
                        downtime_minutes,
                    )
                ),
                performance=0.0,
                quality=0.0,
                oee=0.0,
                runtime_minutes=runtime_minutes,
                downtime_minutes=downtime_minutes,
                total_qty=0,
                ok_qty=0,
                ng_qty=0,
            )

        ideal_seconds = sum(
            row.cycle_time_sec
            * (row.ok_qty + row.ng_qty)
            for row in output_rows
        )

        weighted_cycle_time_sec = (
            ideal_seconds / total_qty
        )

        return (
            OEECalculationService
            .calculate_execution_oee(
                runtime_minutes=runtime_minutes,
                downtime_minutes=downtime_minutes,
                ok_qty=ok_qty,
                ng_qty=ng_qty,
                ideal_cycle_time_sec=(
                    weighted_cycle_time_sec
                ),
            )
        )

    @staticmethod
    def empty_result() -> OEEResult:
        return OEEResult(
            availability=0.0,
            performance=0.0,
            quality=0.0,
            oee=0.0,
            runtime_minutes=0.0,
            downtime_minutes=0.0,
            total_qty=0,
            ok_qty=0,
            ng_qty=0,
        )

    @classmethod
    def _normalize_row(
        cls,
        row,
    ) -> OEEAggregationRow:
        if isinstance(row, dict):
            getter = row.get
        else:
            getter = lambda name: getattr(
                row,
                name,
                None,
            )

        runtime = cls._non_negative_float(
            getter("runtime_minutes"),
            "Runtime Minutes",
        )
        downtime = cls._non_negative_float(
            getter("downtime_minutes"),
            "Downtime Minutes",
        )
        ok_qty = cls._non_negative_int(
            getter("ok_qty"),
            "OK Qty",
        )
        ng_qty = cls._non_negative_int(
            getter("ng_qty"),
            "NG Qty",
        )
        cycle_time = cls._positive_float(
            getter("cycle_time_sec"),
            "Cycle Time Sec",
        )
        operation_no = cls._operation_number(
            getter("operation_no")
        )
        final_value = getter("is_final_operation")

        return OEEAggregationRow(
            runtime_minutes=runtime,
            downtime_minutes=downtime,
            ok_qty=ok_qty,
            ng_qty=ng_qty,
            cycle_time_sec=cycle_time,
            work_order_no=cls._text(
                getter("work_order_no")
            ),
            product_code=cls._text(
                getter("product_code")
            ),
            operation_no=operation_no,
            is_final_operation=(
                cls._boolean(final_value)
                if final_value is not None
                else None
            ),
        )

    @classmethod
    def _select_output_rows(cls, rows):
        """Count output once while retaining time from every OP."""
        if not any(
            row.work_order_no
            or row.product_code
            or row.operation_no is not None
            or row.is_final_operation is not None
            for row in rows
        ):
            return rows

        grouped = {}
        selected = []

        for row in rows:
            has_metadata = (
                row.work_order_no
                or row.product_code
                or row.operation_no is not None
                or row.is_final_operation is not None
            )
            if not has_metadata:
                selected.append(row)
                continue

            key = (
                row.work_order_no,
                row.product_code,
            )
            grouped.setdefault(key, []).append(row)

        for group_rows in grouped.values():
            has_explicit_marker = any(
                row.is_final_operation is not None
                for row in group_rows
            )
            if has_explicit_marker:
                selected.extend(
                    row
                    for row in group_rows
                    if row.is_final_operation is True
                )
                continue

            rows_with_op = [
                row
                for row in group_rows
                if row.operation_no is not None
            ]
            if not rows_with_op:
                selected.extend(group_rows)
                continue

            highest_op = max(
                row.operation_no
                for row in rows_with_op
            )
            selected.extend(
                row
                for row in rows_with_op
                if row.operation_no == highest_op
            )

        return selected

    @staticmethod
    def _non_negative_float(
        value,
        field_name,
    ) -> float:
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
    def _positive_float(
        value,
        field_name,
    ) -> float:
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
    def _non_negative_int(
        value,
        field_name,
    ) -> int:
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

    @staticmethod
    def _operation_number(value):
        if value is None:
            return None

        text = str(value).strip().upper()
        if not text:
            return None

        if text.startswith("OP"):
            text = text[2:].strip()

        try:
            number = int(float(text))
        except (TypeError, ValueError, OverflowError):
            return None

        return number if number >= 0 else None

    @staticmethod
    def _boolean(value):
        if isinstance(value, bool):
            return value

        return str(value or "").strip().upper() in {
            "1",
            "TRUE",
            "YES",
            "Y",
        }

    @staticmethod
    def _text(value):
        return str(value or "").strip().upper()
