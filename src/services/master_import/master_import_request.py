from dataclasses import dataclass


@dataclass(slots=True)
class MasterImportRequest:

    module_name: str = ""

    file_path: str = ""

    sheet_name: str | None = None

    validate_only: bool = False