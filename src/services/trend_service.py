from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
from math import isfinite
from typing import Any, Iterable, Mapping


class TrendGranularity(StrEnum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass(frozen=True, slots=True)
class TrendPoint:
    period_start: datetime
    label: str

    oee: float
    availability: float
    performance: float
    quality: float

    runtime_minutes: float
    downtime_minutes: float

    ok_qty: int
    ng_qty: int
    execution_count: int


class TrendService:
    """
    Tạo dữ liệu xu hướng OEE theo giờ, ngày, tuần hoặc tháng.

    Service chấp nhận cả:
    - dictionary;
    - dataclass;
    - object có thuộc tính tương ứng.

    Các tỷ lệ OEE, Availability, Performance và Quality được tổng hợp
    theo trọng số runtime. Nếu runtime bằng 0, trọng số mặc định là 1.
    """

    DATETIME_FIELDS = (
        "started_at",
        "start_time",
        "execution_time",
        "recorded_at",
        "datetime",
        "date",
        "production_date",
        "ngay",
    )

    def build(
        self,
        rows: Iterable[Any] | None,
        *,
        granularity: TrendGranularity | str = TrendGranularity.DAILY,
        datetime_field: str | None = None,
    ) -> list[TrendPoint]:
        resolved_granularity = self._resolve_granularity(
            granularity
        )

        buckets: dict[datetime, list[Mapping[str, Any]]] = (
            defaultdict(list)
        )
        prepared_rows = []

        for item in rows or []:
            row = dict(self._as_mapping(item))

            timestamp = self._extract_datetime(
                row,
                datetime_field=datetime_field,
            )

            if timestamp is None:
                continue

            timestamp = self._production_timestamp(
                row,
                timestamp,
            )
            prepared_rows.append(
                (row, timestamp)
            )

        output_row_ids = {
            id(row)
            for row in self._select_output_rows(
                [
                    row
                    for row, _ in prepared_rows
                ]
            )
        }

        for row, timestamp in prepared_rows:
            row["__count_final_output__"] = (
                id(row) in output_row_ids
            )
            period_start = self._period_start(
                timestamp,
                resolved_granularity,
            )

            buckets[period_start].append(row)

        result: list[TrendPoint] = []

        for period_start in sorted(buckets):
            period_rows = buckets[period_start]

            result.append(
                self._build_point(
                    period_start=period_start,
                    rows=period_rows,
                    granularity=resolved_granularity,
                )
            )

        return result

    def _build_point(
        self,
        *,
        period_start: datetime,
        rows: list[Mapping[str, Any]],
        granularity: TrendGranularity,
    ) -> TrendPoint:
        runtime_minutes = sum(
            self._number(
                self._first(
                    row,
                    "runtime_minutes",
                    "runtime",
                    "run_minutes",
                )
            )
            for row in rows
        )

        downtime_minutes = sum(
            self._number(
                self._first(
                    row,
                    "downtime_minutes",
                    "downtime",
                    "stop_minutes",
                )
            )
            for row in rows
        )

        output_rows = [
            row
            for row in rows
            if row.get(
                "__count_final_output__",
                True,
            )
        ]
        ok_qty = sum(
            self._integer(
                self._first(
                    row,
                    "ok_qty",
                    "ok_quantity",
                    "quantity_ok",
                    "so_luong_ok",
                )
            )
            for row in output_rows
        )

        ng_qty = sum(
            self._integer(
                self._first(
                    row,
                    "ng_qty",
                    "ng_quantity",
                    "quantity_ng",
                    "total_ng",
                    "tong_ng",
                )
            )
            for row in output_rows
        )

        return TrendPoint(
            period_start=period_start,
            label=self._format_label(
                period_start,
                granularity,
            ),
            oee=self._weighted_metric(rows, "oee"),
            availability=self._weighted_metric(
                rows,
                "availability",
            ),
            performance=self._weighted_metric(
                rows,
                "performance",
            ),
            quality=(
                self._output_quality(output_rows)
                if any(
                    self._has_route_metadata(row)
                    for row in rows
                )
                else self._weighted_metric(
                    rows,
                    "quality",
                )
            ),
            runtime_minutes=round(runtime_minutes, 2),
            downtime_minutes=round(downtime_minutes, 2),
            ok_qty=ok_qty,
            ng_qty=ng_qty,
            execution_count=len(rows),
        )

    def _weighted_metric(
        self,
        rows: list[Mapping[str, Any]],
        field: str,
    ) -> float:
        weighted_total = 0.0
        total_weight = 0.0

        for row in rows:
            value = self._number(row.get(field))

            runtime = self._number(
                self._first(
                    row,
                    "runtime_minutes",
                    "runtime",
                    "run_minutes",
                )
            )

            weight = runtime if runtime > 0 else 1.0

            weighted_total += value * weight
            total_weight += weight

        if total_weight <= 0:
            return 0.0

        return round(
            weighted_total / total_weight,
            4,
        )

    def _extract_datetime(
        self,
        row: Mapping[str, Any],
        *,
        datetime_field: str | None,
    ) -> datetime | None:
        fields: tuple[str, ...]

        if datetime_field:
            fields = (datetime_field,)
        else:
            fields = self.DATETIME_FIELDS

        for field in fields:
            if field not in row:
                continue

            parsed = self._to_datetime(row.get(field))

            if parsed is not None:
                return parsed

        return None

    @staticmethod
    def _period_start(
        value: datetime,
        granularity: TrendGranularity,
    ) -> datetime:
        if granularity == TrendGranularity.HOURLY:
            return value.replace(
                minute=0,
                second=0,
                microsecond=0,
            )

        if granularity == TrendGranularity.DAILY:
            return value.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        if granularity == TrendGranularity.WEEKLY:
            week_start = value.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            return week_start.replace(
                day=week_start.day
            ) - __import__(
                "datetime"
            ).timedelta(days=week_start.weekday())

        if granularity == TrendGranularity.MONTHLY:
            return value.replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        if granularity == TrendGranularity.YEARLY:
            return value.replace(
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        raise ValueError(
            f"Granularity không được hỗ trợ: {granularity}"
        )

    @staticmethod
    def _format_label(
        period_start: datetime,
        granularity: TrendGranularity,
    ) -> str:
        if granularity == TrendGranularity.HOURLY:
            return period_start.strftime(
                "%d/%m/%Y %H:00"
            )

        if granularity == TrendGranularity.DAILY:
            return period_start.strftime(
                "%d/%m/%Y"
            )

        if granularity == TrendGranularity.WEEKLY:
            year, week, _ = period_start.isocalendar()
            return f"Tuần {week:02d}/{year}"

        if granularity == TrendGranularity.MONTHLY:
            return period_start.strftime(
                "%m/%Y"
            )

        if granularity == TrendGranularity.YEARLY:
            return period_start.strftime("%Y")

        return str(period_start)

    @staticmethod
    def _resolve_granularity(
        value: TrendGranularity | str,
    ) -> TrendGranularity:
        if isinstance(value, TrendGranularity):
            return value

        try:
            return TrendGranularity(
                str(value).strip().lower()
            )
        except ValueError as exc:
            raise ValueError(
                "Granularity phải là hourly, daily, "
                "weekly, monthly hoặc yearly."
            ) from exc

    @classmethod
    def _production_timestamp(
        cls,
        row: Mapping[str, Any],
        timestamp: datetime,
    ) -> datetime:
        shift = str(
            cls._first(
                row,
                "shift",
                "production_shift",
                "ca",
            )
            or ""
        ).strip().upper()

        if (
            shift in {
                "NIGHT",
                "N",
                "ĐÊM",
                "CA ĐÊM",
            }
            and timestamp.hour < 8
        ):
            return timestamp - timedelta(days=1)

        return timestamp

    @classmethod
    def _select_output_rows(
        cls,
        rows: list[Mapping[str, Any]],
    ) -> list[Mapping[str, Any]]:
        if not any(
            cls._has_route_metadata(row)
            for row in rows
        ):
            return rows

        grouped = {}
        selected = []

        for row in rows:
            if cls._is_excluded(row):
                continue

            if not cls._has_route_metadata(row):
                selected.append(row)
                continue

            key = (
                cls._text(
                    cls._first(
                        row,
                        "work_order_no",
                        "work_order",
                    )
                ),
                cls._text(
                    cls._first(
                        row,
                        "product_code",
                        "product",
                    )
                ),
            )
            grouped.setdefault(key, []).append(row)

        for group_rows in grouped.values():
            marked = [
                row
                for row in group_rows
                if cls._boolean(
                    cls._first(
                        row,
                        "is_final_operation",
                        "is_final_op",
                    )
                )
            ]
            has_marker = any(
                cls._first(
                    row,
                    "is_final_operation",
                    "is_final_op",
                )
                is not None
                for row in group_rows
            )
            if has_marker:
                selected.extend(marked)
                continue

            with_op = [
                (
                    cls._operation_number(
                        cls._first(
                            row,
                            "operation_no",
                            "op_no",
                            "operation",
                        )
                    ),
                    row,
                )
                for row in group_rows
            ]
            with_op = [
                item
                for item in with_op
                if item[0] is not None
            ]
            if not with_op:
                selected.extend(group_rows)
                continue

            highest_op = max(
                op_no
                for op_no, _ in with_op
            )
            selected.extend(
                row
                for op_no, row in with_op
                if op_no == highest_op
            )

        return selected

    @classmethod
    def _output_quality(
        cls,
        rows: list[Mapping[str, Any]],
    ) -> float:
        ok_qty = sum(
            cls._integer(
                cls._first(
                    row,
                    "ok_qty",
                    "ok_quantity",
                    "quantity_ok",
                    "so_luong_ok",
                )
            )
            for row in rows
        )
        ng_qty = sum(
            cls._integer(
                cls._first(
                    row,
                    "ng_qty",
                    "ng_quantity",
                    "quantity_ng",
                    "total_ng",
                    "tong_ng",
                )
            )
            for row in rows
        )
        total_qty = ok_qty + ng_qty

        if total_qty > 0:
            return round(
                ok_qty / total_qty * 100.0,
                4,
            )

        return 0.0

    @classmethod
    def _has_route_metadata(
        cls,
        row: Mapping[str, Any],
    ) -> bool:
        return any(
            cls._first(row, *fields) is not None
            for fields in (
                ("work_order_no", "work_order"),
                ("product_code", "product"),
                ("operation_no", "op_no", "operation"),
                ("is_final_operation", "is_final_op"),
            )
        )

    @classmethod
    def _is_excluded(
        cls,
        row: Mapping[str, Any],
    ) -> bool:
        status = cls._text(
            cls._first(
                row,
                "execution_status",
                "status",
            )
        )
        routing_status = cls._text(
            cls._first(
                row,
                "routing_status",
                "operation_status",
            )
        )
        return (
            status in {"RUNNING", "CANCELLED"}
            or routing_status == "INACTIVE"
        )

    @staticmethod
    def _operation_number(value: Any) -> int | None:
        text = str(value or "").strip().upper()
        if text.startswith("OP"):
            text = text[2:].strip()

        try:
            number = int(float(text))
        except (TypeError, ValueError, OverflowError):
            return None

        return number if number >= 0 else None

    @staticmethod
    def _boolean(value: Any) -> bool:
        if isinstance(value, bool):
            return value

        return str(value or "").strip().upper() in {
            "1",
            "TRUE",
            "YES",
            "Y",
        }

    @staticmethod
    def _text(value: Any) -> str:
        return str(value or "").strip().upper()

    @staticmethod
    def _to_datetime(
        value: Any,
    ) -> datetime | None:
        if isinstance(value, datetime):
            return value

        if isinstance(value, date):
            return datetime.combine(
                value,
                datetime.min.time(),
            )

        if value is None:
            return None

        text = str(value).strip()

        if not text:
            return None

        formats = (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
        )

        for date_format in formats:
            try:
                return datetime.strptime(
                    text,
                    date_format,
                )
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None

    @staticmethod
    def _as_mapping(
        value: Any,
    ) -> Mapping[str, Any]:
        if isinstance(value, Mapping):
            return value

        if is_dataclass(value):
            return asdict(value)

        if hasattr(value, "__dict__"):
            return vars(value)

        return {}

    @staticmethod
    def _first(
        row: Mapping[str, Any],
        *fields: str,
    ) -> Any:
        for field in fields:
            value = row.get(field)

            if value is not None:
                return value

        return None

    @staticmethod
    def _number(
        value: Any,
    ) -> float:
        try:
            number = float(value or 0)
        except (TypeError, ValueError, OverflowError):
            return 0.0

        return number if isfinite(number) else 0.0

    @classmethod
    def _integer(
        cls,
        value: Any,
    ) -> int:
        return int(round(cls._number(value)))
