from __future__ import annotations

import pandas as pd

from .base_validator import BaseValidator
from .validation_error import ValidationError


class DuplicateValidator(BaseValidator):
    """
    Kiểm tra các cột Unique.
    """

    def __init__(
        self,
        schema,
    ):
        self.schema = schema

    def validate(
        self,
        dataframe,
        result,
    ):

        for field_name in self.schema.unique_fields:

            if field_name not in dataframe.columns:
                continue

            series = dataframe[field_name]

            duplicated = series.duplicated(
                keep=False
            )

            for index, is_duplicate in enumerate(
                duplicated
            ):

                if not is_duplicate:
                    continue

                value = series.iloc[index]

                if self._is_empty(value):
                    continue

                result.add_error(
                    ValidationError(
                        row=index + 2,
                        column=field_name,
                        code="DUPLICATE_VALUE",
                        message=(
                            f"Duplicate value "
                            f"'{value}'."
                        ),
                        value=value,
                        validator="DuplicateValidator",
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