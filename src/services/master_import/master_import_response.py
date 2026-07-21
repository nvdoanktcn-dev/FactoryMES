from dataclasses import dataclass, field


@dataclass(slots=True)
class MasterImportResponse:
    success: bool = True
    message: str = ""

    preview_rows: list = field(
        default_factory=list
    )

    validation_errors: list = field(
        default_factory=list
    )

    validation_warnings: list = field(
        default_factory=list
    )

    sheet_names: list = field(
        default_factory=list
    )

    headers: list = field(
        default_factory=list
    )

    total_rows: int = 0
    header_row: int = 0

    imported_rows: int = 0
    failed_rows: int = 0

    duration: float = 0.0