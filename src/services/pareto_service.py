from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, is_dataclass
from math import isfinite
from typing import Any

from src.services.ranking_service import (
    RankingItem,
    RankingService,
)


class ParetoService:
    """
    Xây dựng dữ liệu Pareto từ danh sách bản ghi.

    Có thể nhóm theo:
        machine
        product
        work_order
        operator
        ng_type
    """

    @classmethod
    def build(
        cls,
        rows: Iterable[Any],
        *,
        group_field: str,
        value_field: str,
    ) -> tuple[RankingItem, ...]:

        normalized_rows = [
            cls._as_mapping(row)
            for row in rows or []
        ]
        output_rows = cls._select_output_rows(
            normalized_rows
        )
        grouped: dict[str, float] = defaultdict(float)

        for row in output_rows:
            name = str(row.get(group_field, ""))
            value = row.get(value_field, 0)

            try:
                number = float(value or 0)
            except (TypeError, ValueError, OverflowError):
                number = 0.0

            if not isfinite(number):
                number = 0.0

            grouped[name] += max(number, 0.0)

        ranking_rows = [
            {
                "name": key,
                "value": value,
            }
            for key, value in grouped.items()
        ]

        return RankingService.build(
            ranking_rows,
            key="name",
            value="value",
        )

    @classmethod
    def _select_output_rows(cls, rows):
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
                selected.extend(
                    row
                    for row in group_rows
                    if cls._boolean(
                        cls._first(
                            row,
                            "is_final_operation",
                            "is_final_op",
                        )
                    )
                )
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

    @staticmethod
    def _as_mapping(row):
        if isinstance(row, dict):
            return row

        if is_dataclass(row):
            return asdict(row)

        if hasattr(row, "__dict__"):
            return vars(row)

        return {}

    @classmethod
    def _has_route_metadata(cls, row):
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
    def _is_excluded(cls, row):
        return (
            cls._text(
                cls._first(
                    row,
                    "execution_status",
                    "status",
                )
            )
            in {"RUNNING", "CANCELLED"}
            or cls._text(
                cls._first(
                    row,
                    "routing_status",
                    "operation_status",
                )
            )
            == "INACTIVE"
        )

    @staticmethod
    def _first(row, *fields):
        for field in fields:
            value = row.get(field)
            if value is not None:
                return value

        return None

    @staticmethod
    def _operation_number(value):
        text = str(value or "").strip().upper()
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
