from __future__ import annotations

import time

from .datatype_validator import (
    DataTypeValidator,
)
from .duplicate_validator import (
    DuplicateValidator,
)
from .header_validator import (
    HeaderValidator,
)
from .required_field_validator import (
    RequiredFieldValidator,
)
from .validation_result import (
    ValidationResult,
)


class ValidationService:
    """
    Điều phối toàn bộ validator của một ImportSchema.
    """

    def __init__(
        self,
        schema,
        validators=None,
    ):
        self.schema = schema

        self.validators = (
            validators
            or [
                HeaderValidator(schema),
                RequiredFieldValidator(schema),
                DuplicateValidator(schema),
                DataTypeValidator(schema),
            ]
        )

    def validate(
        self,
        dataframe,
    ):
        start = time.perf_counter()

        result = ValidationResult(
            checked_rows=len(
                dataframe
            )
        )

        for validator in self.validators:
            validator.validate(
                dataframe,
                result,
            )

        result.duration = (
            time.perf_counter()
            - start
        )

        result.success = (
            len(result.errors) == 0
        )

        return result