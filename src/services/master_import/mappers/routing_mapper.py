from __future__ import annotations

import re

from src.domain.entities import Routing

from .base_mapper import BaseMapper


class RoutingMapper(BaseMapper):
    def from_row(
        self,
        row,
    ):
        cycle_time = self._to_float(
            row.get(
                "Standard Cycle Time (Sec)"
            ),
            default=0.0,
        )

        standard_output = self._to_float(
            row.get(
                "Standard Output (PCS/H)"
            ),
            default=0.0,
        )

        if (
            standard_output <= 0
            and cycle_time > 0
        ):
            standard_output = (
                3600.0 / cycle_time
            )

        return Routing(
            product_code=self._text(
                row.get(
                    "Product Code"
                )
            ).upper(),

            operation_no=self._operation_no(
                row.get(
                    "Operation No"
                )
            ),

            operation_name=self._text(
                row.get(
                    "Operation Name"
                )
            ),

            process_type=self._text(
                row.get(
                    "Process Type"
                )
            ).upper(),

            machine_type=self._text(
                row.get(
                    "Machine Type"
                )
            ).upper(),

            standard_cycle_time_sec=cycle_time,

            standard_output_pcs_hour=standard_output,

            standard_operator_count=self._to_float(
                row.get(
                    "Standard Operator Count"
                ),
                default=1.0,
            ),

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
                row.get(
                    "Remark"
                )
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

    @classmethod
    def _operation_no(
        cls,
        value,
    ):
        text = cls._text(
            value
        ).upper()

        match = re.fullmatch(
            r"OP\s*(\d+)",
            text,
        )

        if match:
            return int(
                match.group(1)
            )

        try:
            operation_no = int(
                float(text)
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"Invalid Operation No: {value}"
            ) from error

        if operation_no <= 0:
            raise ValueError(
                "Operation No must be greater than zero."
            )

        return operation_no

    @staticmethod
    def _to_float(
        value,
        default=0.0,
    ):
        if value is None:
            return float(
                default
            )

        text = str(
            value
        ).strip()

        if (
            not text
            or text.lower()
            in {
                "nan",
                "none",
                "nat",
            }
        ):
            return float(
                default
            )

        try:
            return float(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"Invalid numeric value: {value}"
            ) from error