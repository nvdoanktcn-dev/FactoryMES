from __future__ import annotations

from src.domain.entities import Employee

from .base_mapper import BaseMapper


class EmployeeMapper(BaseMapper):
    def from_row(
        self,
        row,
    ):
        return Employee(
            employee_code=self._text(
                row.get("Employee Code")
            ).upper(),

            employee_name=self._text(
                row.get("Employee Name")
            ),

            department=self._text(
                row.get("Department")
            ),

            position=self._text(
                row.get("Position")
            ),

            shift=self._text(
                row.get("Shift")
            ).upper(),

            status=(
                self._text(
                    row.get(
                        "Status",
                        "ACTIVE",
                    )
                ).upper()
                or "ACTIVE"
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

        text = str(
            value
        ).strip()

        if text.lower() in {
            "nan",
            "none",
            "nat",
        }:
            return ""

        return text