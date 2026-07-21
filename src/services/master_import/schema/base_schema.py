from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class FieldSchema:
    """
    Quy tắc validation cho một cột Excel.
    """

    name: str
    required: bool = False
    data_type: type | None = None
    default: Any = None

    aliases: list[str] = field(
        default_factory=list
    )

    validators: list[Callable] = field(
        default_factory=list
    )

    unique: bool = False

    allowed_values: list[Any] | None = None

    minimum: float | int | None = None
    maximum: float | int | None = None

    min_length: int | None = None
    max_length: int | None = None

    def all_names(self) -> list[str]:
        return [
            self.name,
            *self.aliases,
        ]


@dataclass
class ImportSchema:
    """
    Schema hoàn chỉnh cho một module Master Import.
    """

    module_name: str

    fields: list[FieldSchema] = field(
        default_factory=list
    )

    allow_extra_columns: bool = True

    def __post_init__(self):
        self.module_name = str(
            self.module_name or ""
        ).strip().upper()

        if not self.module_name:
            raise ValueError(
                "ImportSchema.module_name is required."
            )
    @property
    def headers(self) -> list[str]:
        """
        Backward-compatible alias.
        """
        return [
            item.name
            for item in self.fields
        ]

    @property
    def required_headers(self) -> list[str]:
        return [
            item.name
            for item in self.fields
            if item.required
        ]

    @property
    def optional_headers(self) -> list[str]:
        return [
            item.name
            for item in self.fields
            if not item.required
        ]

    @property
    def unique_fields(self) -> list[str]:
        """
        Danh sách tên cột cần kiểm tra trùng trong file.
        """

        return [
            item.name
            for item in self.fields
            if item.unique
        ]

    @property
    def field_names(self) -> list[str]:
        """
        Alias tương thích cho danh sách header.
        """

        return self.headers

    @property
    def field_map(self) -> dict[str, FieldSchema]:
        """
        Truy cập nhanh FieldSchema theo tên cột chính.
        """

        return {
            item.name: item
            for item in self.fields
        }   

    @property
    def required_columns(self) -> list[str]:
        return self.required_headers

    @property
    def optional_columns(self) -> list[str]:
        return self.optional_headers

    @property
    def all_columns(self) -> list[str]:
        return self.headers

    def get_field(
        self,
        column_name,
    ) -> FieldSchema | None:
        normalized = self.normalize_text(
            column_name
        ).lower()

        for item in self.fields:
            names = [
                self.normalize_text(
                    name
                ).lower()
                for name in item.all_names()
            ]

            if normalized in names:
                return item

        return None

    @staticmethod
    def normalize_text(
        value,
    ) -> str:
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


# Alias tương thích nếu module nào đó còn import BaseSchema.
BaseSchema = ImportSchema