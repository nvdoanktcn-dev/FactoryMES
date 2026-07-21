from __future__ import annotations

from datetime import date, datetime

from src.domain.entities import WorkOrder

from .base_mapper import BaseMapper


class WorkOrderMapper(BaseMapper):
    def from_row(
        self,
        row,
    ):
        return WorkOrder(
            work_order_no=self._text(
                row.get("Work Order No")
            ).upper(),

            product_code=self._text(
                row.get("Product Code")
            ).upper(),

            plan_qty=self._to_int(
                row.get("Plan Qty")
            ),

            start_date=self._to_date(
                row.get("Start Date")
            ),

            due_date=self._to_date(
                row.get("Due Date")
            ),

            priority=(
                self._text(
                    row.get(
                        "Priority",
                        "NORMAL",
                    )
                ).upper()
                or "NORMAL"
            ),

            status=(
                self._text(
                    row.get(
                        "Status",
                        "PLANNED",
                    )
                ).upper()
                or "PLANNED"
            ),

            remark=self._text(
                row.get("Remark")
            ),
        )

    @staticmethod
    def _text(
        value,
    ):
        if value is None:
            return ""

        text = str(value).strip()

        if text.lower() in {
            "nan",
            "none",
            "nat",
        }:
            return ""

        return text

    @classmethod
    def _to_int(
        cls,
        value,
    ):
        text = cls._text(value)

        try:
            result = int(float(text))
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"Invalid Plan Qty: {value}"
            ) from error

        if result <= 0:
            raise ValueError(
                "Plan Qty must be greater than zero."
            )

        return result

    @classmethod
    def _to_date(
        cls,
        value,
    ):
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        text = cls._text(value)

        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
        ]

        for date_format in formats:
            try:
                return datetime.strptime(
                    text,
                    date_format,
                ).date()
            except ValueError:
                continue

        raise ValueError(
            f"Invalid date: {value}"
        )