from __future__ import annotations

from types import SimpleNamespace

from src.services.master_import.validation.base_validator import BaseValidator
from src.services.master_import.validation.validation_error import ValidationError

class HeaderValidator(BaseValidator):

    def __init__(
        self,
        schema=None,
        required_headers=None,
        headers=None,
        allow_extra_columns=True,
    ):
        if schema is not None:
            self.schema = schema
        else:
            expected = headers or required_headers or []

            self.schema = SimpleNamespace(
                headers=expected,
                required_headers=required_headers or expected,
                allow_extra_columns=allow_extra_columns,
            )

    def validate(self, dataframe, result):
        headers = [
            str(column).strip()
            for column in dataframe.columns
        ]

        expected_headers = self.schema.headers

        required_headers = self.schema.required_headers

        for header in required_headers:
            if header not in headers:
                result.add_error(
                    ValidationError(
                            row=0,
                        column=header,
                        code="HEADER_MISSING",
                        message=f"Missing column '{header}'.",
                        validator="HeaderValidator",
                    )
                )

        if not self.schema.allow_extra_columns:
            for header in headers:
                if header not in expected_headers:
                    result.add_error(
                        ValidationError(
                            row=0,
                            column=header,
                            code="UNKNOWN_COLUMN",
                            message=f"Unknown column '{header}'.",
                            validator="HeaderValidator",
                        )
                    )

        seen = set()

        for header in headers:
            normalized = header.casefold()

            if normalized in seen:
                result.add_error(
                        ValidationError(
                        row=0,
                        column=header,
                        code="DUPLICATE_COLUMN",
                            message=f"Duplicate column '{header}'.",
                        validator="HeaderValidator",
                    )
                )    

            seen.add(normalized)