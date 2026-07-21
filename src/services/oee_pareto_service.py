from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable, Mapping, Sequence


Number = int | float | Decimal


@dataclass(frozen=True, slots=True)
class ParetoResultItem:
    """
    Một dòng kết quả Pareto đã được tổng hợp.
    """

    label: str
    value: float
    cumulative_value: float
    cumulative_percent: float
    rank: int

    def to_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "value": self.value,
            "cumulative_value": self.cumulative_value,
            "cumulative_percent": self.cumulative_percent,
            "rank": self.rank,
        }


@dataclass(frozen=True, slots=True)
class ParetoResult:
    """
    Kết quả hoàn chỉnh của một phép phân tích Pareto.
    """

    items: tuple[ParetoResultItem, ...]
    total_value: float
    focus_item_count: int
    focus_threshold: float
    source_record_count: int
    ignored_record_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "items": [
                item.to_dict()
                for item in self.items
            ],
            "total_value": self.total_value,
            "focus_item_count": self.focus_item_count,
            "focus_threshold": self.focus_threshold,
            "source_record_count": self.source_record_count,
            "ignored_record_count": self.ignored_record_count,
        }


@dataclass(frozen=True, slots=True)
class ParetoFilter:
    """
    Bộ lọc tùy chọn cho dữ liệu Pareto.

    Mã máy, nhân viên, công lệnh và sản phẩm được giữ nguyên
    chữ hoa/chữ thường sau khi chuẩn hóa. Việc so khớp trong
    service vẫn không phân biệt hoa/thường.
    """

    start_date: date | datetime | None = None
    end_date: date | datetime | None = None
    machine_codes: tuple[str, ...] = ()
    employee_codes: tuple[str, ...] = ()
    work_order_codes: tuple[str, ...] = ()
    product_codes: tuple[str, ...] = ()

    def normalized(self) -> "ParetoFilter":
        start_date = self._normalize_date(
            self.start_date
        )
        end_date = self._normalize_date(
            self.end_date
        )

        if (
            start_date is not None
            and end_date is not None
            and start_date > end_date
        ):
            raise ValueError(
                "start_date must be before or equal to end_date."
            )

        return ParetoFilter(
            start_date=start_date,
            end_date=end_date,
            machine_codes=self._normalize_codes(
                self.machine_codes
            ),
            employee_codes=self._normalize_codes(
                self.employee_codes
            ),
            work_order_codes=self._normalize_codes(
                self.work_order_codes
            ),
            product_codes=self._normalize_codes(
                self.product_codes
            ),
        )

    @staticmethod
    def _normalize_date(
        value: date | datetime | None,
    ) -> date | None:
        if value is None:
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        raise TypeError(
            (
                "Date filter value must be date, datetime, "
                f"or None, not {type(value).__name__}."
            )
        )

    @staticmethod
    def _normalize_codes(
        values: Sequence[str],
    ) -> tuple[str, ...]:
        """
        Làm sạch mã nhưng không thay đổi chữ hoa/chữ thường.

        Loại bỏ:
        - khoảng trắng đầu/cuối;
        - giá trị rỗng;
        - mã trùng nhau không phân biệt hoa/thường.

        Khi có mã trùng khác kiểu chữ, giá trị xuất hiện đầu tiên
        được giữ lại.
        """

        normalized: dict[str, str] = {}

        for value in values:
            text = str(value).strip()

            if not text:
                continue

            comparison_key = text.casefold()

            if comparison_key not in normalized:
                normalized[comparison_key] = text

        return tuple(
            sorted(
                normalized.values(),
                key=str.casefold,
            )
        )


class OEEParetoService:
    """
    Service tổng hợp Pareto cho OEE Dashboard.

    Service không phụ thuộc SQLAlchemy hoặc UI. Dữ liệu đầu vào có thể là:
    - Mapping/dictionary
    - SQLAlchemy model
    - dataclass
    - object thông thường có attribute tương ứng

    Các API chính:
        build_downtime_pareto(records, ...)
        build_ng_pareto(records, ...)
        build_generic_pareto(records, ...)

    Tên field mặc định hỗ trợ nhiều alias để tương thích với các model khác nhau.
    """

    DEFAULT_DOWNTIME_LABEL_FIELDS = (
        "reason",
        "downtime_reason",
        "reason_name",
        "category",
        "name",
        "label",
    )
    DEFAULT_DOWNTIME_VALUE_FIELDS = (
        "duration_minutes",
        "downtime_minutes",
        "minutes",
        "duration",
        "value",
    )
    DEFAULT_NG_LABEL_FIELDS = (
        "reason",
        "ng_reason",
        "defect_reason",
        "defect_type",
        "category",
        "name",
        "label",
    )
    DEFAULT_NG_VALUE_FIELDS = (
        "quantity",
        "ng_quantity",
        "defect_quantity",
        "count",
        "value",
    )
    DEFAULT_DATE_FIELDS = (
        "production_date",
        "record_date",
        "event_date",
        "date",
        "started_at",
        "created_at",
    )
    DEFAULT_MACHINE_FIELDS = (
        "machine_code",
        "device_code",
        "machine",
    )
    DEFAULT_EMPLOYEE_FIELDS = (
        "employee_code",
        "operator_code",
        "employee",
        "operator",
    )
    DEFAULT_WORK_ORDER_FIELDS = (
        "work_order_code",
        "work_order",
        "production_order_code",
    )
    DEFAULT_PRODUCT_FIELDS = (
        "product_code",
        "product",
        "item_code",
    )

    def build_downtime_pareto(
        self,
        records: Iterable[object],
        *,
        filters: ParetoFilter | None = None,
        label_fields: Sequence[str] | None = None,
        value_fields: Sequence[str] | None = None,
        maximum_items: int | None = None,
        focus_threshold: float = 80.0,
        unknown_label: str = "Không xác định",
        include_zero: bool = False,
    ) -> ParetoResult:
        """
        Tổng hợp thời gian dừng máy theo nguyên nhân.
        """

        return self.build_generic_pareto(
            records=records,
            label_fields=(
                label_fields
                or self.DEFAULT_DOWNTIME_LABEL_FIELDS
            ),
            value_fields=(
                value_fields
                or self.DEFAULT_DOWNTIME_VALUE_FIELDS
            ),
            filters=filters,
            maximum_items=maximum_items,
            focus_threshold=focus_threshold,
            unknown_label=unknown_label,
            include_zero=include_zero,
        )

    def build_ng_pareto(
        self,
        records: Iterable[object],
        *,
        filters: ParetoFilter | None = None,
        label_fields: Sequence[str] | None = None,
        value_fields: Sequence[str] | None = None,
        maximum_items: int | None = None,
        focus_threshold: float = 80.0,
        unknown_label: str = "Không xác định",
        include_zero: bool = False,
    ) -> ParetoResult:
        """
        Tổng hợp số lượng NG theo nguyên nhân.
        """

        return self.build_generic_pareto(
            records=records,
            label_fields=(
                label_fields
                or self.DEFAULT_NG_LABEL_FIELDS
            ),
            value_fields=(
                value_fields
                or self.DEFAULT_NG_VALUE_FIELDS
            ),
            filters=filters,
            maximum_items=maximum_items,
            focus_threshold=focus_threshold,
            unknown_label=unknown_label,
            include_zero=include_zero,
        )

    def build_generic_pareto(
        self,
        records: Iterable[object],
        *,
        label_fields: Sequence[str],
        value_fields: Sequence[str],
        filters: ParetoFilter | None = None,
        maximum_items: int | None = None,
        focus_threshold: float = 80.0,
        unknown_label: str = "Không xác định",
        include_zero: bool = False,
    ) -> ParetoResult:
        """
        Tổng hợp Pareto từ một tập bản ghi bất kỳ.
        """

        normalized_label_fields = self._normalize_field_names(
            label_fields,
            argument_name="label_fields",
        )
        normalized_value_fields = self._normalize_field_names(
            value_fields,
            argument_name="value_fields",
        )

        if maximum_items is not None and maximum_items < 1:
            raise ValueError(
                "maximum_items must be at least 1."
            )

        if not 0 < focus_threshold <= 100:
            raise ValueError(
                "focus_threshold must be greater than 0 and at most 100."
            )

        normalized_unknown_label = (
            str(unknown_label).strip()
            or "Không xác định"
        )
        normalized_filters = (
            filters.normalized()
            if filters is not None
            else ParetoFilter().normalized()
        )

        grouped_values: dict[str, float] = {}
        source_record_count = 0
        ignored_record_count = 0

        for record in records:
            source_record_count += 1

            if not self._matches_filters(
                record,
                normalized_filters,
            ):
                ignored_record_count += 1
                continue

            raw_value = self._read_first_value(
                record,
                normalized_value_fields,
            )

            if raw_value is None:
                ignored_record_count += 1
                continue

            try:
                value = self._to_non_negative_float(
                    raw_value
                )
            except (TypeError, ValueError):
                ignored_record_count += 1
                continue

            if value == 0 and not include_zero:
                ignored_record_count += 1
                continue

            raw_label = self._read_first_value(
                record,
                normalized_label_fields,
            )
            label = self._normalize_label(
                raw_label,
                normalized_unknown_label,
            )

            grouped_values[label] = (
                grouped_values.get(label, 0.0)
                + value
            )

        ordered = sorted(
            grouped_values.items(),
            key=lambda item: (
                -item[1],
                item[0].casefold(),
            ),
        )

        if (
            maximum_items is not None
            and len(ordered) > maximum_items
        ):
            ordered = self._group_remaining_as_other(
                ordered,
                maximum_items,
            )

        total_value = sum(
            value
            for _, value in ordered
        )
        cumulative_value = 0.0
        result_items: list[ParetoResultItem] = []
        focus_item_count = 0

        for index, (label, value) in enumerate(
            ordered,
            start=1,
        ):
            cumulative_value += value
            cumulative_percent = (
                cumulative_value
                / total_value
                * 100.0
                if total_value > 0
                else 0.0
            )

            result_items.append(
                ParetoResultItem(
                    label=label,
                    value=value,
                    cumulative_value=cumulative_value,
                    cumulative_percent=cumulative_percent,
                    rank=index,
                )
            )

            if (
                focus_item_count == 0
                and cumulative_percent >= focus_threshold
            ):
                focus_item_count = index

        if result_items and focus_item_count == 0:
            focus_item_count = len(result_items)

        return ParetoResult(
            items=tuple(result_items),
            total_value=total_value,
            focus_item_count=focus_item_count,
            focus_threshold=float(focus_threshold),
            source_record_count=source_record_count,
            ignored_record_count=ignored_record_count,
        )

    def to_chart_items(
        self,
        result: ParetoResult,
    ) -> list[dict[str, object]]:
        """
        Chuyển kết quả service sang cấu trúc mà ParetoChart nhận trực tiếp.
        """

        if not isinstance(result, ParetoResult):
            raise TypeError(
                "result must be ParetoResult."
            )

        return [
            {
                "label": item.label,
                "value": item.value,
            }
            for item in result.items
        ]

    def _matches_filters(
        self,
        record: object,
        filters: ParetoFilter,
    ) -> bool:
        record_date = self._extract_record_date(
            record
        )

        if (
            filters.start_date is not None
            and (
                record_date is None
                or record_date < filters.start_date
            )
        ):
            return False

        if (
            filters.end_date is not None
            and (
                record_date is None
                or record_date > filters.end_date
            )
        ):
            return False

        if not self._matches_code_filter(
            record,
            self.DEFAULT_MACHINE_FIELDS,
            filters.machine_codes,
        ):
            return False

        if not self._matches_code_filter(
            record,
            self.DEFAULT_EMPLOYEE_FIELDS,
            filters.employee_codes,
        ):
            return False

        if not self._matches_code_filter(
            record,
            self.DEFAULT_WORK_ORDER_FIELDS,
            filters.work_order_codes,
        ):
            return False

        if not self._matches_code_filter(
            record,
            self.DEFAULT_PRODUCT_FIELDS,
            filters.product_codes,
        ):
            return False

        return True

    def _extract_record_date(
        self,
        record: object,
    ) -> date | None:
        raw_value = self._read_first_value(
            record,
            self.DEFAULT_DATE_FIELDS,
        )

        if raw_value is None:
            return None

        if isinstance(raw_value, datetime):
            return raw_value.date()

        if isinstance(raw_value, date):
            return raw_value

        if isinstance(raw_value, str):
            stripped = raw_value.strip()

            if not stripped:
                return None

            for parser in (
                date.fromisoformat,
                lambda value: datetime.fromisoformat(
                    value
                ).date(),
            ):
                try:
                    parsed = parser(stripped)
                except ValueError:
                    continue

                return (
                    parsed.date()
                    if isinstance(parsed, datetime)
                    else parsed
                )

        return None

    def _matches_code_filter(
        self,
        record: object,
        field_names: Sequence[str],
        accepted_codes: Sequence[str],
    ) -> bool:
        if not accepted_codes:
            return True

        raw_value = self._read_first_value(
            record,
            field_names,
        )

        if raw_value is None:
            return False

        code = self._extract_code(
            raw_value
        )

        if code is None:
            return False

        accepted_keys = {
            accepted_code.casefold()
            for accepted_code in accepted_codes
        }

        return code.casefold() in accepted_keys

    def _extract_code(
        self,
        value: object,
    ) -> str | None:
        if value is None:
            return None

        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None

        if isinstance(value, Mapping):
            for field_name in (
                "code",
                "machine_code",
                "employee_code",
                "work_order_code",
                "product_code",
                "name",
            ):
                if field_name in value:
                    return self._extract_code(
                        value[field_name]
                    )

            return None

        for field_name in (
            "code",
            "machine_code",
            "employee_code",
            "work_order_code",
            "product_code",
            "name",
        ):
            if hasattr(value, field_name):
                return self._extract_code(
                    getattr(value, field_name)
                )

        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def _normalize_field_names(
        field_names: Sequence[str],
        *,
        argument_name: str,
    ) -> tuple[str, ...]:
        normalized = tuple(
            str(field_name).strip()
            for field_name in field_names
            if str(field_name).strip()
        )

        if not normalized:
            raise ValueError(
                f"{argument_name} must not be empty."
            )

        return normalized

    @staticmethod
    def _normalize_label(
        raw_label: object,
        unknown_label: str,
    ) -> str:
        if raw_label is None:
            return unknown_label

        if isinstance(raw_label, Mapping):
            for field_name in (
                "name",
                "label",
                "reason",
                "code",
            ):
                if field_name in raw_label:
                    return OEEParetoService._normalize_label(
                        raw_label[field_name],
                        unknown_label,
                    )

        for field_name in (
            "name",
            "label",
            "reason",
            "code",
        ):
            if hasattr(raw_label, field_name):
                return OEEParetoService._normalize_label(
                    getattr(raw_label, field_name),
                    unknown_label,
                )

        normalized = str(raw_label).strip()

        return normalized or unknown_label

    @staticmethod
    def _to_non_negative_float(
        raw_value: object,
    ) -> float:
        if isinstance(raw_value, bool):
            raise TypeError(
                "Boolean is not a valid Pareto value."
            )

        value = float(raw_value)

        if value < 0:
            raise ValueError(
                "Pareto value must be non-negative."
            )

        if value != value:
            raise ValueError(
                "Pareto value must not be NaN."
            )

        if value in (
            float("inf"),
            float("-inf"),
        ):
            raise ValueError(
                "Pareto value must be finite."
            )

        return value

    @staticmethod
    def _read_first_value(
        record: object,
        field_names: Sequence[str],
    ) -> object | None:
        for field_name in field_names:
            value = OEEParetoService._read_value(
                record,
                field_name,
            )

            if value is not None:
                return value

        return None

    @staticmethod
    def _read_value(
        record: object,
        field_name: str,
    ) -> object | None:
        if isinstance(record, Mapping):
            return record.get(field_name)

        return getattr(
            record,
            field_name,
            None,
        )

    @staticmethod
    def _group_remaining_as_other(
        ordered: list[tuple[str, float]],
        maximum_items: int,
    ) -> list[tuple[str, float]]:
        if maximum_items == 1:
            total = sum(
                value
                for _, value in ordered
            )

            return [
                (
                    "Khác",
                    total,
                )
            ]

        visible_count = maximum_items - 1
        visible_items = ordered[
            :visible_count
        ]
        remaining_items = ordered[
            visible_count:
        ]
        other_value = sum(
            value
            for _, value in remaining_items
        )

        return [
            *visible_items,
            (
                "Khác",
                other_value,
            ),
        ]
