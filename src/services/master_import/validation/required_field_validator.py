from __future__ import annotations

import pandas as pd

from .base_validator import BaseValidator
from .validation_error import ValidationError


class RequiredFieldValidator(BaseValidator):
    """
    Kiểm tra các cột bắt buộc.
    """

    def __init__(self, schema):
        self.schema = schema

    def validate(
        self,
        dataframe,
        result,
    ):

        required_fields = [
            field
            for field in self.schema.fields
            if field.required
        ]

        for field in required_fields:

            if field.name not in dataframe.columns:
                continue

            series = dataframe[field.name]

            for index, value in enumerate(series):

                if self._is_empty(value):

                    result.add_error(
                        ValidationError(
                            row=index + 2,
                            column=field.name,
                            code="REQUIRED_FIELD",
                            message=(
                                f"'{field.name}' "
                                "cannot be empty."
                            ),
                            value=value,
                            validator="RequiredFieldValidator",
                        )
                    )

    @staticmethod
    def _is_empty(value):

        if value is None:
            return True

        if pd.isna(value):
            return True

        if isinstance(value, str):

            if value.strip() == "":
                return True

        return False