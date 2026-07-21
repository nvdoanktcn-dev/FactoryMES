from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ImportResult:
    """
    Kết quả thực thi Import Engine.
    """

    success: bool = True

    module_name: str = ""

    total_rows: int = 0

    inserted_rows: int = 0

    updated_rows: int = 0

    skipped_rows: int = 0

    failed_rows: int = 0

    duration: float = 0.0

    transaction_id: str = ""

    messages: list[str] = field(
        default_factory=list
    )

    errors: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    details: list[dict[str, Any]] = field(
        default_factory=list
    )

    def add_message(
        self,
        message,
    ):
        text = str(
            message or ""
        ).strip()

        if text:
            self.messages.append(
                text
            )

    def add_warning(
        self,
        message,
    ):
        text = str(
            message or ""
        ).strip()

        if text:
            self.warnings.append(
                text
            )

    def add_error(
        self,
        message,
    ):
        text = str(
            message or ""
        ).strip()

        self.success = False

        if text:
            self.errors.append(
                text
            )

    def add_detail(
        self,
        detail,
    ):
        if isinstance(
            detail,
            dict,
        ):
            self.details.append(
                detail
            )

    def finalize(self):
        """
        Đồng bộ trạng thái cuối của kết quả.
        """

        if self.errors:
            self.success = False

        processed_rows = (
            self.inserted_rows
            + self.updated_rows
            + self.skipped_rows
            + self.failed_rows
        )

        if (
            self.total_rows > 0
            and processed_rows < self.total_rows
        ):
            self.add_warning(
                (
                    f"{self.total_rows - processed_rows} "
                    "row(s) have no final status."
                )
            )

        return self