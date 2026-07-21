from __future__ import annotations

import pandas as pd

from .base_validator import BaseValidator
from .validation_error import ValidationError


class DataTypeValidator(BaseValidator):
    """
    Kiểm tra kiểu dữ liệu và giới hạn giá trị.
    """

    def __init__(self, schema):
        self.schema = schema

    def validate(
        self,
        dataframe,
        result,
    ):

        for field in self.schema.fields:

            if field.name not in dataframe.columns:
                continue

            series = dataframe[field.name]

            for index, value in enumerate(series):

                if self._is_empty(value):
                    continue

                row_number = index + 2

                # -------------------------
                # String
                # -------------------------

                if field.data_type is str:

                    text = str(value).strip()

                    if (
                        field.allowed_values
                    ):

                        allowed = [
                            str(x).upper()
                            for x in field.allowed_values
                        ]

                        if text.upper() not in allowed:

                            result.add_error(
                                ValidationError(
                                    row=row_number,
                                    column=field.name,
                                    code="INVALID_VALUE",
                                    message=(
                                        f"'{text}' "
                                        "is not allowed."
                                    ),
                                    value=value,
                                    validator="DataTypeValidator",
                                )
                            )

                # -------------------------
                # Float
                # -------------------------

                elif field.data_type is float:

                    try:

                        number = float(
                            value
                        )

                    except Exception:

                        result.add_error(
                            ValidationError(
                                row=row_number,
                                column=field.name,
                                code="INVALID_TYPE",
                                message=(
                                    "Must be numeric."
                                ),
                                value=value,
                                validator="DataTypeValidator",
                            )
                        )

                        continue

                    if (
                        field.minimum
                        is not None
                    ):

                        if (
                            number
                            < field.minimum
                        ):

                            result.add_error(
                                ValidationError(
                                    row=row_number,
                                    column=field.name,
                                    code="MINIMUM",
                                    message=(
                                        f"Minimum is "
                                        f"{field.minimum}"
                                    ),
                                    value=value,
                                    validator="DataTypeValidator",
                                )
                            )

                    if (
                        field.maximum
                        is not None
                    ):

                        if (
                            number
                            > field.maximum
                        ):

                            result.add_error(
                                ValidationError(
                                    row=row_number,
                                    column=field.name,
                                    code="MAXIMUM",
                                    message=(
                                        f"Maximum is "
                                        f"{field.maximum}"
                                    ),
                                    value=value,
                                    validator="DataTypeValidator",
                                )
                            )

                # -------------------------
                # Integer
                # -------------------------

                elif field.data_type is int:

                    try:

                        int(value)

                    except Exception:

                        result.add_error(
                            ValidationError(
                                row=row_number,
                                column=field.name,
                                code="INVALID_TYPE",
                                message="Must be integer.",
                                value=value,
                                validator="DataTypeValidator",
                            )
                        )

    @staticmethod
    def _is_empty(value):

        if value is None:
            return True

        if pd.isna(value):
            return True

        if isinstance(value, str):

            return value.strip() == ""

        return False