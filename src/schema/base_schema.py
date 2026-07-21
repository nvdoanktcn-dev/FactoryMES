from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class FieldSchema:
    """
    Cấu hình cho một cột import.
    """

    name: str
    required: bool = False
    data_type: type = str
    unique: bool = False
    allowed_values: list[Any] = field(
        default_factory=list
    )
    minimum: float | None = None
    maximum: float | None = None


@dataclass(slots=True)
class ImportSchema:
    """
    Cấu hình import cho một module.
    """

    module_name: str
    fields: list[FieldSchema]
    allow_extra_columns: bool = False

    @property
    def headers(self) -> list[str]:
        return [
            field.name
            for field in self.fields
        ]

    @property
    def required_headers(self) -> list[str]:
        return [
            field.name
            for field in self.fields
            if field.required
        ]

    @property
    def unique_fields(self) -> list[str]:
        return [
            field.name
            for field in self.fields
            if field.unique
        ]

    def field(
        self,
        name: str,
    ) -> FieldSchema | None:
        normalized = str(
            name or ""
        ).strip()

        for field_schema in self.fields:
            if field_schema.name == normalized:
                return field_schema

        return None