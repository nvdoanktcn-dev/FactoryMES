from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class OEEDashboardFilters:
    start_date: date
    end_date: date

    machine_code: str | None = None
    employee_code: str | None = None
    shift: str | None = None
    work_order_no: str | None = None
    product_code: str | None = None
    operation_no: str | int | None = None

    def __post_init__(self) -> None:
        if self.start_date > self.end_date:
            raise ValueError(
                "Ngày bắt đầu không được lớn hơn ngày kết thúc."
            )

    @staticmethod
    def _normalize_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()

        if not normalized:
            return None

        if normalized.casefold() in {
            "tất cả",
            "tat ca",
            "all",
        }:
            return None

        return normalized

    @classmethod
    def _normalize_operation(
        cls,
        value: str | int | None,
    ) -> int | None:
        if value is None:
            return None

        if isinstance(value, int):
            if value < 0:
                raise ValueError(
                    "Operation number không được âm."
                )
            return value

        normalized = cls._normalize_text(
            value
        )

        if normalized is None:
            return None

        match = re.fullmatch(
            r"(?:OP\s*)?(\d+)",
            normalized,
            flags=re.IGNORECASE,
        )

        if match is None:
            raise ValueError(
                f"Operation không hợp lệ: {value!r}"
            )

        return int(match.group(1))

    def to_service_kwargs(
        self,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "start_at": self.start_date,
            "end_at": self.end_date,
        }

        text_fields = (
            "machine_code",
            "employee_code",
            "shift",
            "work_order_no",
            "product_code",
        )

        for field_name in text_fields:
            value = self._normalize_text(
                getattr(self, field_name)
            )

            if value is not None:
                kwargs[field_name] = value

        operation_no = self._normalize_operation(
            self.operation_no
        )

        if operation_no is not None:
            kwargs["operation_no"] = operation_no

        return kwargs


@dataclass(slots=True)
class OEEDashboardData:
    summary: Mapping[str, Any] = field(
        default_factory=dict
    )

    trend: list[Mapping[str, Any]] = field(
        default_factory=list
    )

    by_machine: list[Mapping[str, Any]] = field(
        default_factory=list
    )

    by_employee: list[Mapping[str, Any]] = field(
        default_factory=list
    )

    by_work_order: list[Mapping[str, Any]] = field(
        default_factory=list
    )

    by_product: list[Mapping[str, Any]] = field(
        default_factory=list
    )

    by_operation: list[Mapping[str, Any]] = field(
        default_factory=list
    )