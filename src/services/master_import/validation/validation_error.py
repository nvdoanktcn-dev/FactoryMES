from dataclasses import dataclass


@dataclass(slots=True)
class ValidationError:
    """
    Một lỗi validation.
    """

    row: int

    column: str

    code: str

    message: str

    severity: str = "ERROR"

    value: object | None = None

    validator: str = ""