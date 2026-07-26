from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from math import isfinite
from typing import Any, Iterable, Mapping


class ProgressStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_TRACK = "on_track"
    COMPLETED = "completed"
    OVER_COMPLETED = "over_completed"


@dataclass(frozen=True, slots=True)
class ProgressItem:
    work_order: str
    product: str

    planned_qty: int
    completed_qty: int
    remaining_qty: int
    over_completed_qty: int

    progress_percent: float
    display_percent: float

    status: ProgressStatus


class ProgressService:
    """
    Tổng hợp tiến độ sản xuất theo Work Order.

    Quy tắc:
    - Một Work Order tương ứng một Product.
    - Sản lượng hoàn thành được cộng từ completed_qty.
    - remaining_qty không nhỏ hơn 0.
    - progress_percent có thể lớn hơn 100%.
    - display_percent giới hạn trong khoảng 0–100 để dùng cho QProgressBar.
    """

    WORK_ORDER_FIELDS = (
        "work_order",
        "work_order_no",
        "order_code",
        "production_order",
        "ma_cong_lenh",
    )

    PRODUCT_FIELDS = (
        "product",
        "product_code",
        "product_name",
        "ten_san_pham",
    )

    PLANNED_FIELDS = (
        "planned_qty",
        "plan_qty",
        "target_qty",
        "order_qty",
        "quantity_plan",
        "so_luong_ke_hoach",
    )

    COMPLETED_FIELDS = (
        "completed_qty",
        "actual_qty",
        "finished_qty",
        "output_qty",
        "ok_qty",
        "ok_quantity",
        "quantity_completed",
        "so_luong_hoan_thanh",
    )

    OP_FIELDS = (
        "op_no",
        "operation_no",
        "operation",
        "process_no",
    )

    STATUS_FIELDS = (
        "execution_status",
        "status",
    )

    FINAL_OPERATION_FIELDS = (
        "is_final_operation",
        "is_final_op",
        "final_operation",
    )

    ROUTING_STATUS_FIELDS = (
        "routing_status",
        "operation_status",
    )

    PLAN_DATE_FIELDS = (
        "plan_date",
        "planned_date",
        "effective_date",
        "updated_at",
    )

    def build(
        self,
        rows: Iterable[Any] | None,
    ) -> list[ProgressItem]:
        grouped: dict[str, dict[str, Any]] = {}

        for item in rows or []:
            row = self._as_mapping(item)

            work_order = self._text(
                self._first(
                    row,
                    *self.WORK_ORDER_FIELDS,
                )
            )

            if not work_order:
                continue

            product = self._text(
                self._first(
                    row,
                    *self.PRODUCT_FIELDS,
                )
            )

            planned_qty = self._integer(
                self._first(
                    row,
                    *self.PLANNED_FIELDS,
                )
            )

            completed_qty = self._integer(
                self._first(
                    row,
                    *self.COMPLETED_FIELDS,
                )
            )

            bucket = grouped.setdefault(
                work_order,
                {
                    "work_order": work_order,
                    "product": product,
                    "planned_qty": 0,
                    "completed_qty": 0,
                    "rows": [],
                },
            )

            if product:
                if (
                    bucket["product"]
                    and bucket["product"] != product
                ):
                    raise ValueError(
                        (
                            "A Work Order must belong to exactly "
                            f"one Product: {work_order} has "
                            f"{bucket['product']} and {product}."
                        )
                    )
                bucket["product"] = product

            bucket["rows"].append(
                {
                    "row": row,
                    "planned_qty": max(
                        planned_qty,
                        0,
                    ),
                    "completed_qty": max(
                        completed_qty,
                        0,
                    ),
                    "op_no": self._operation_number(
                        self._first(
                            row,
                            *self.OP_FIELDS,
                        )
                    ),
                    "status": self._text(
                        self._first(
                            row,
                            *self.STATUS_FIELDS,
                        )
                    ).upper(),
                    "is_final": self._boolean(
                        self._first(
                            row,
                            *self.FINAL_OPERATION_FIELDS,
                        )
                    ),
                    "routing_status": self._text(
                        self._first(
                            row,
                            *self.ROUTING_STATUS_FIELDS,
                        )
                    ).upper(),
                    "plan_date": self._date_value(
                        self._first(
                            row,
                            *self.PLAN_DATE_FIELDS,
                        )
                    ),
                }
            )

        for bucket in grouped.values():
            bucket["planned_qty"] = (
                self._latest_planned_qty(
                    bucket["rows"]
                )
            )
            bucket["completed_qty"] = (
                self._final_completed_qty(
                    bucket["rows"]
                )
            )

        result = [
            self._build_item(bucket)
            for bucket in grouped.values()
        ]

        return sorted(
            result,
            key=lambda item: (
                item.status == ProgressStatus.COMPLETED,
                item.status == ProgressStatus.OVER_COMPLETED,
                -item.remaining_qty,
                item.work_order,
            ),
        )

    def build_one(
        self,
        row: Any,
    ) -> ProgressItem | None:
        items = self.build([row])

        if not items:
            return None

        return items[0]

    def _build_item(
        self,
        bucket: Mapping[str, Any],
    ) -> ProgressItem:
        planned_qty = max(
            self._integer(
                bucket.get("planned_qty")
            ),
            0,
        )

        completed_qty = max(
            self._integer(
                bucket.get("completed_qty")
            ),
            0,
        )

        remaining_qty = max(
            planned_qty - completed_qty,
            0,
        )

        over_completed_qty = max(
            completed_qty - planned_qty,
            0,
        )

        progress_percent = self._progress_percent(
            planned_qty=planned_qty,
            completed_qty=completed_qty,
        )

        display_percent = min(
            max(progress_percent, 0.0),
            100.0,
        )

        return ProgressItem(
            work_order=self._text(
                bucket.get("work_order")
            ),
            product=self._text(
                bucket.get("product")
            ),
            planned_qty=planned_qty,
            completed_qty=completed_qty,
            remaining_qty=remaining_qty,
            over_completed_qty=over_completed_qty,
            progress_percent=progress_percent,
            display_percent=round(
                display_percent,
                2,
            ),
            status=self._status(
                planned_qty=planned_qty,
                completed_qty=completed_qty,
                progress_percent=progress_percent,
            ),
        )

    @staticmethod
    def _progress_percent(
        *,
        planned_qty: int,
        completed_qty: int,
    ) -> float:
        if planned_qty <= 0:
            return 0.0

        return round(
            completed_qty / planned_qty * 100.0,
            2,
        )

    @staticmethod
    def _status(
        *,
        planned_qty: int,
        completed_qty: int,
        progress_percent: float,
    ) -> ProgressStatus:
        if planned_qty > 0 and completed_qty > planned_qty:
            return ProgressStatus.OVER_COMPLETED

        if planned_qty > 0 and completed_qty == planned_qty:
            return ProgressStatus.COMPLETED

        if progress_percent >= 80:
            return ProgressStatus.ON_TRACK

        if completed_qty > 0:
            return ProgressStatus.IN_PROGRESS

        return ProgressStatus.NOT_STARTED

    @staticmethod
    def _as_mapping(
        value: Any,
    ) -> Mapping[str, Any]:
        if isinstance(value, Mapping):
            return value

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
    def _text(
        value: Any,
    ) -> str:
        return str(value or "").strip()

    @staticmethod
    def _integer(
        value: Any,
    ) -> int:
        try:
            number = float(value or 0)
            if not isfinite(number):
                return 0
            return int(round(number))
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return 0

    @classmethod
    def _latest_planned_qty(
        cls,
        rows,
    ) -> int:
        dated_rows = [
            row
            for row in rows
            if row["plan_date"] is not None
        ]
        if dated_rows:
            latest_date = max(
                row["plan_date"]
                for row in dated_rows
            )
            return max(
                row["planned_qty"]
                for row in dated_rows
                if row["plan_date"] == latest_date
            )

        return max(
            (
                row["planned_qty"]
                for row in rows
            ),
            default=0,
        )

    @classmethod
    def _final_completed_qty(
        cls,
        rows,
    ) -> int:
        eligible = [
            row
            for row in rows
            if row["status"] != "CANCELLED"
            and row["routing_status"] != "INACTIVE"
        ]

        explicit_final = [
            row
            for row in eligible
            if row["is_final"]
        ]
        if explicit_final:
            eligible = explicit_final
        else:
            operation_rows = [
                row
                for row in eligible
                if row["op_no"] is not None
            ]
            if operation_rows:
                highest_op = max(
                    row["op_no"]
                    for row in operation_rows
                )
                eligible = [
                    row
                    for row in operation_rows
                    if row["op_no"] == highest_op
                ]

        return sum(
            row["completed_qty"]
            for row in eligible
            if row["status"] != "RUNNING"
        )

    @staticmethod
    def _operation_number(
        value,
    ) -> int | None:
        text = str(value or "").strip().upper()
        digits = "".join(
            character
            for character in text
            if character.isdigit()
        )
        return int(digits) if digits else None

    @staticmethod
    def _boolean(value) -> bool:
        if isinstance(value, bool):
            return value
        return str(value or "").strip().upper() in {
            "1",
            "TRUE",
            "YES",
            "Y",
        }

    @staticmethod
    def _date_value(value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(
                value,
                datetime.min.time(),
            )
        if value is None or value == "":
            return None
        try:
            return datetime.fromisoformat(
                str(value).strip()
            )
        except (TypeError, ValueError):
            return None
