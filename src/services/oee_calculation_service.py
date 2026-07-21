from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from typing import Any, Iterable, Optional

from sqlalchemy.orm import Session

from src.database.session import SessionLocal
from src.models.production_assignment import ProductionAssignment
from src.models.production_execution import ProductionExecution
from src.models.production_order import ProductionOrder


@dataclass(frozen=True)
class OEESummary:
    """
    Kết quả OEE trong một phạm vi dữ liệu.

    Các tỷ lệ được lưu dưới dạng phần trăm từ 0 đến 100.
    """

    execution_count: int
    planned_minutes: float
    runtime_minutes: float
    downtime_minutes: float
    ok_quantity: int
    ng_quantity: int
    total_quantity: int
    ideal_runtime_minutes: float
    availability: float
    performance: float
    quality: float
    oee: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OEEGroupResult:
    group_key: str
    group_name: str
    summary: OEESummary

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_key": self.group_key,
            "group_name": self.group_name,
            **self.summary.to_dict(),
        }


class OEECalculationService:
    """
    Tính OEE từ Production Execution.

    Công thức:

        Availability
            = Runtime / Planned Production Time

        Performance
            = Ideal Runtime / Runtime

        Quality
            = OK Quantity / Total Quantity

        OEE
            = Availability × Performance × Quality

    Quy ước:

    - planned_minutes = runtime_minutes + downtime_minutes.
    - total_quantity = ok_quantity + ng_quantity.
    - ideal_runtime_minutes được tính từ cycle time chuẩn.
    - Tất cả kết quả phần trăm được giới hạn trong 0..100.
    - Bản ghi CANCELLED không tham gia tính toán.
    """

    EXCLUDED_EXECUTION_STATUSES = {
        "CANCELLED",
    }

    # Các tên cột có thể dùng trong những phiên bản model khác nhau.
    OK_QTY_FIELDS = (
        "ok_qty",
        "good_qty",
        "actual_ok_qty",
        "production_ok_qty",
    )

    TOTAL_NG_FIELDS = (
        "total_ng_qty",
        "ng_qty",
        "defect_qty",
    )

    PROCESSING_NG_FIELDS = (
        "processing_ng_qty",
        "machining_ng_qty",
    )

    BLANK_NG_FIELDS = (
        "blank_ng_qty",
        "casting_ng_qty",
    )

    RUNTIME_FIELDS = (
        "runtime_minutes",
        "run_time_minutes",
        "actual_runtime_minutes",
    )

    DOWNTIME_FIELDS = (
        "downtime_minutes",
        "down_time_minutes",
    )

    CYCLE_TIME_SECOND_FIELDS = (
        "standard_cycle_time_seconds",
        "standard_cycle_time_sec",
        "cycle_time_seconds",
        "cycle_time_sec",
        "standard_seconds_per_piece",
    )

    CYCLE_TIME_MINUTE_FIELDS = (
        "standard_cycle_time_minutes",
        "cycle_time_minutes",
        "standard_minutes_per_piece",
    )

    OPERATION_NUMBER_FIELDS = (
        "operation_no",
        "op_no",
        "operation_number",
    )

    def __init__(
        self,
        session: Optional[Session] = None,
    ):
        self._owns_session = session is None
        self.session = session or SessionLocal()

    # ==========================================================
    # Public API
    # ==========================================================

    def calculate_summary(
        self,
        *,
        start_at: Optional[datetime | date | str] = None,
        end_at: Optional[datetime | date | str] = None,
        machine_code: Optional[str] = None,
        employee_code: Optional[str] = None,
        shift: Optional[str] = None,
        work_order_no: Optional[str] = None,
        product_code: Optional[str] = None,
        operation_no: Optional[str | int] = None,
    ) -> OEESummary:
        rows = self._load_rows(
            start_at=start_at,
            end_at=end_at,
            machine_code=machine_code,
            employee_code=employee_code,
            shift=shift,
            work_order_no=work_order_no,
            product_code=product_code,
            operation_no=operation_no,
        )

        return self._calculate_rows(
            rows
        )

    def calculate_by_machine(
        self,
        *,
        start_at: Optional[datetime | date | str] = None,
        end_at: Optional[datetime | date | str] = None,
        machine_code: Optional[str] = None,
    ) -> list[OEEGroupResult]:
        rows = self._load_rows(
            start_at=start_at,
            end_at=end_at,
            machine_code=machine_code,
        )

        return self._group_rows(
            rows,
            key_getter=lambda row: self._text(
                row["assignment"].machine_code
                if row["assignment"] is not None
                else ""
            ),
            name_getter=lambda row: self._text(
                row["assignment"].machine_code
                if row["assignment"] is not None
                else ""
            ),
        )

    def calculate_by_employee(
        self,
        *,
        start_at: Optional[datetime | date | str] = None,
        end_at: Optional[datetime | date | str] = None,
        employee_code: Optional[str] = None,
    ) -> list[OEEGroupResult]:
        rows = self._load_rows(
            start_at=start_at,
            end_at=end_at,
            employee_code=employee_code,
        )

        return self._group_rows(
            rows,
            key_getter=lambda row: self._text(
                row["assignment"].employee_code
                if row["assignment"] is not None
                else ""
            ),
            name_getter=lambda row: self._text(
                row["assignment"].employee_code
                if row["assignment"] is not None
                else ""
            ),
        )

    def calculate_by_work_order(
        self,
        *,
        start_at: Optional[datetime | date | str] = None,
        end_at: Optional[datetime | date | str] = None,
        work_order_no: Optional[str] = None,
    ) -> list[OEEGroupResult]:
        rows = self._load_rows(
            start_at=start_at,
            end_at=end_at,
            work_order_no=work_order_no,
        )

        return self._group_rows(
            rows,
            key_getter=lambda row: self._text(
                row["production_order"].work_order_no
                if row["production_order"] is not None
                else ""
            ),
            name_getter=lambda row: self._text(
                row["production_order"].work_order_no
                if row["production_order"] is not None
                else ""
            ),
        )

    def calculate_by_product(
        self,
        *,
        start_at: Optional[datetime | date | str] = None,
        end_at: Optional[datetime | date | str] = None,
        product_code: Optional[str] = None,
    ) -> list[OEEGroupResult]:
        rows = self._load_rows(
            start_at=start_at,
            end_at=end_at,
            product_code=product_code,
        )

        return self._group_rows(
            rows,
            key_getter=lambda row: self._text(
                row["production_order"].product_code
                if row["production_order"] is not None
                else ""
            ),
            name_getter=lambda row: self._text(
                row["production_order"].product_code
                if row["production_order"] is not None
                else ""
            ),
        )

    def calculate_by_operation(
        self,
        *,
        start_at: Optional[datetime | date | str] = None,
        end_at: Optional[datetime | date | str] = None,
        operation_no: Optional[str | int] = None,
    ) -> list[OEEGroupResult]:
        rows = self._load_rows(
            start_at=start_at,
            end_at=end_at,
            operation_no=operation_no,
        )

        def operation_key(row: dict[str, Any]) -> str:
            production_order = row["production_order"]

            if production_order is None:
                return ""

            value = self._first_value(
                production_order,
                self.OPERATION_NUMBER_FIELDS,
                default="",
            )

            return self._normalize_operation(
                value
            )

        def operation_name(row: dict[str, Any]) -> str:
            production_order = row["production_order"]

            if production_order is None:
                return ""

            key = operation_key(row)
            name = self._text(
                getattr(
                    production_order,
                    "operation_name",
                    "",
                )
            )

            if name:
                return f"{key} - {name}"

            return key

        return self._group_rows(
            rows,
            key_getter=operation_key,
            name_getter=operation_name,
        )

    def close(self) -> None:
        if self._owns_session:
            self.session.close()

    # ==========================================================
    # Query
    # ==========================================================

    def _load_rows(
        self,
        *,
        start_at: Optional[datetime | date | str] = None,
        end_at: Optional[datetime | date | str] = None,
        machine_code: Optional[str] = None,
        employee_code: Optional[str] = None,
        shift: Optional[str] = None,
        work_order_no: Optional[str] = None,
        product_code: Optional[str] = None,
        operation_no: Optional[str | int] = None,
    ) -> list[dict[str, Any]]:
        start_dt = self._parse_start_datetime(
            start_at
        )
        end_dt = self._parse_end_datetime(
            end_at
        )

        query = (
            self.session
            .query(
                ProductionExecution,
                ProductionAssignment,
                ProductionOrder,
            )
            .outerjoin(
                ProductionAssignment,
                ProductionAssignment.id
                == ProductionExecution.assignment_id,
            )
            .outerjoin(
                ProductionOrder,
                ProductionOrder.id
                == ProductionAssignment.production_order_id,
            )
        )

        if start_dt is not None:
            query = query.filter(
                ProductionExecution.start_time
                >= start_dt
            )

        if end_dt is not None:
            query = query.filter(
                ProductionExecution.start_time
                <= end_dt
            )

        if machine_code:
            query = query.filter(
                ProductionAssignment.machine_code
                == self._normalize_code(machine_code)
            )

        if employee_code:
            query = query.filter(
                ProductionAssignment.employee_code
                == self._normalize_code(employee_code)
            )

        if shift:
            query = query.filter(
                ProductionAssignment.shift
                == self._normalize_code(shift)
            )

        if work_order_no:
            query = query.filter(
                ProductionOrder.work_order_no
                == self._normalize_code(work_order_no)
            )

        if product_code:
            query = query.filter(
                ProductionOrder.product_code
                == self._normalize_code(product_code)
            )

        result_rows = []

        for (
            execution,
            assignment,
            production_order,
        ) in query.all():
            status = self._normalize_code(
                getattr(
                    execution,
                    "status",
                    "",
                )
            )

            if status in self.EXCLUDED_EXECUTION_STATUSES:
                continue

            if operation_no is not None:
                row_operation = self._normalize_operation(
                    self._first_value(
                        production_order,
                        self.OPERATION_NUMBER_FIELDS,
                        default="",
                    )
                    if production_order is not None
                    else ""
                )

                required_operation = self._normalize_operation(
                    operation_no
                )

                if row_operation != required_operation:
                    continue

            result_rows.append(
                {
                    "execution": execution,
                    "assignment": assignment,
                    "production_order": production_order,
                }
            )

        return result_rows

    # ==========================================================
    # Calculation
    # ==========================================================

    def _calculate_rows(
        self,
        rows: Iterable[dict[str, Any]],
    ) -> OEESummary:
        execution_count = 0
        runtime_minutes = 0.0
        downtime_minutes = 0.0
        ok_quantity = 0
        ng_quantity = 0
        ideal_runtime_minutes = 0.0

        for row in rows:
            execution = row["execution"]
            production_order = row["production_order"]

            execution_count += 1

            row_runtime = self._non_negative_float(
                self._first_value(
                    execution,
                    self.RUNTIME_FIELDS,
                    default=0,
                )
            )

            row_downtime = self._non_negative_float(
                self._first_value(
                    execution,
                    self.DOWNTIME_FIELDS,
                    default=0,
                )
            )

            row_ok = self._non_negative_int(
                self._first_value(
                    execution,
                    self.OK_QTY_FIELDS,
                    default=0,
                )
            )

            row_ng = self._read_ng_quantity(
                execution
            )

            cycle_time_minutes = (
                self._read_cycle_time_minutes(
                    production_order
                )
            )

            runtime_minutes += row_runtime
            downtime_minutes += row_downtime
            ok_quantity += row_ok
            ng_quantity += row_ng

            total_row_quantity = (
                row_ok
                + row_ng
            )

            ideal_runtime_minutes += (
                cycle_time_minutes
                * total_row_quantity
            )

        planned_minutes = (
            runtime_minutes
            + downtime_minutes
        )

        total_quantity = (
            ok_quantity
            + ng_quantity
        )

        availability = self._safe_percent(
            runtime_minutes,
            planned_minutes,
        )

        performance = self._safe_percent(
            ideal_runtime_minutes,
            runtime_minutes,
        )

        quality = self._safe_percent(
            ok_quantity,
            total_quantity,
        )

        oee = self._clamp_percent(
            (
                availability
                * performance
                * quality
            )
            / 10_000
        )

        return OEESummary(
            execution_count=execution_count,
            planned_minutes=round(
                planned_minutes,
                2,
            ),
            runtime_minutes=round(
                runtime_minutes,
                2,
            ),
            downtime_minutes=round(
                downtime_minutes,
                2,
            ),
            ok_quantity=ok_quantity,
            ng_quantity=ng_quantity,
            total_quantity=total_quantity,
            ideal_runtime_minutes=round(
                ideal_runtime_minutes,
                2,
            ),
            availability=round(
                availability,
                2,
            ),
            performance=round(
                performance,
                2,
            ),
            quality=round(
                quality,
                2,
            ),
            oee=round(
                oee,
                2,
            ),
        )

    def _group_rows(
        self,
        rows: Iterable[dict[str, Any]],
        *,
        key_getter,
        name_getter,
    ) -> list[OEEGroupResult]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        names: dict[str, str] = {}

        for row in rows:
            key = self._text(
                key_getter(row)
            )

            if not key:
                key = "UNASSIGNED"

            name = self._text(
                name_getter(row)
            ) or key

            grouped.setdefault(
                key,
                [],
            ).append(
                row
            )
            names[key] = name

        results = [
            OEEGroupResult(
                group_key=key,
                group_name=names[key],
                summary=self._calculate_rows(
                    group_rows
                ),
            )
            for key, group_rows in grouped.items()
        ]

        results.sort(
            key=lambda item: (
                item.summary.oee,
                item.summary.total_quantity,
                item.group_key,
            ),
            reverse=True,
        )

        return results

    # ==========================================================
    # Field readers
    # ==========================================================

    def _read_ng_quantity(
        self,
        execution: ProductionExecution,
    ) -> int:
        total_ng = self._first_existing_value(
            execution,
            self.TOTAL_NG_FIELDS,
        )

        if total_ng is not None:
            return self._non_negative_int(
                total_ng
            )

        processing_ng = self._non_negative_int(
            self._first_value(
                execution,
                self.PROCESSING_NG_FIELDS,
                default=0,
            )
        )

        blank_ng = self._non_negative_int(
            self._first_value(
                execution,
                self.BLANK_NG_FIELDS,
                default=0,
            )
        )

        return (
            processing_ng
            + blank_ng
        )

    def _read_cycle_time_minutes(
        self,
        production_order: Optional[ProductionOrder],
    ) -> float:
        if production_order is None:
            return 0.0

        minute_value = self._first_existing_value(
            production_order,
            self.CYCLE_TIME_MINUTE_FIELDS,
        )

        if minute_value is not None:
            return self._non_negative_float(
                minute_value
            )

        second_value = self._first_existing_value(
            production_order,
            self.CYCLE_TIME_SECOND_FIELDS,
        )

        if second_value is not None:
            return (
                self._non_negative_float(
                    second_value
                )
                / 60.0
            )

        return 0.0

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _first_existing_value(
        obj: Any,
        field_names: Iterable[str],
    ) -> Any:
        if obj is None:
            return None

        for field_name in field_names:
            if hasattr(
                obj,
                field_name,
            ):
                value = getattr(
                    obj,
                    field_name,
                )

                if value is not None:
                    return value

        return None

    @classmethod
    def _first_value(
        cls,
        obj: Any,
        field_names: Iterable[str],
        *,
        default: Any,
    ) -> Any:
        value = cls._first_existing_value(
            obj,
            field_names,
        )

        return (
            default
            if value is None
            else value
        )

    @staticmethod
    def _safe_percent(
        numerator: float,
        denominator: float,
    ) -> float:
        if denominator <= 0:
            return 0.0

        return OEECalculationService._clamp_percent(
            numerator
            / denominator
            * 100.0
        )

    @staticmethod
    def _clamp_percent(
        value: float,
    ) -> float:
        return max(
            0.0,
            min(
                100.0,
                float(value),
            ),
        )

    @staticmethod
    def _non_negative_float(
        value: Any,
    ) -> float:
        try:
            return max(
                0.0,
                float(
                    value
                    or 0
                ),
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _non_negative_int(
        value: Any,
    ) -> int:
        try:
            return max(
                0,
                int(
                    float(
                        value
                        or 0
                    )
                ),
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0

    @staticmethod
    def _text(
        value: Any,
    ) -> str:
        return str(
            value
            or ""
        ).strip()

    @classmethod
    def _normalize_code(
        cls,
        value: Any,
    ) -> str:
        return cls._text(
            value
        ).upper()

    @classmethod
    def _normalize_operation(
        cls,
        value: Any,
    ) -> str:
        text = cls._normalize_code(
            value
        )

        if not text:
            return ""

        if text.startswith(
            "OP"
        ):
            number_text = text[2:]
        else:
            number_text = text

        try:
            return f"OP{int(number_text):02d}"
        except ValueError:
            return text

    @staticmethod
    def _parse_start_datetime(
        value: Optional[datetime | date | str],
    ) -> Optional[datetime]:
        if value is None:
            return None

        parsed = OEECalculationService._parse_datetime(
            value
        )

        if isinstance(
            value,
            date,
        ) and not isinstance(
            value,
            datetime,
        ):
            return datetime.combine(
                value,
                time.min,
            )

        return parsed

    @staticmethod
    def _parse_end_datetime(
        value: Optional[datetime | date | str],
    ) -> Optional[datetime]:
        if value is None:
            return None

        if isinstance(
            value,
            date,
        ) and not isinstance(
            value,
            datetime,
        ):
            return datetime.combine(
                value,
                time.max,
            )

        if isinstance(
            value,
            str,
        ):
            stripped = value.strip()

            if len(stripped) == 10:
                parsed_date = date.fromisoformat(
                    stripped
                )

                return datetime.combine(
                    parsed_date,
                    time.max,
                )

        return OEECalculationService._parse_datetime(
            value
        )

    @staticmethod
    def _parse_datetime(
        value: datetime | date | str,
    ) -> datetime:
        if isinstance(
            value,
            datetime,
        ):
            return value

        if isinstance(
            value,
            date,
        ):
            return datetime.combine(
                value,
                time.min,
            )

        text = str(
            value
        ).strip()

        if not text:
            raise ValueError(
                "Datetime value cannot be empty."
            )

        try:
            return datetime.fromisoformat(
                text
            )
        except ValueError as error:
            raise ValueError(
                (
                    "Invalid datetime value: "
                    f"{value}"
                )
            ) from error
