from dataclasses import dataclass, field

from .validation_error import ValidationError


@dataclass(slots=True)
class ValidationResult:
    """
    Kết quả validation.
    """

    success: bool = True

    checked_rows: int = 0

    duration: float = 0.0

    errors: list[ValidationError] = field(
        default_factory=list
    )

    warnings: list[ValidationError] = field(
        default_factory=list
    )

    def add_error(
        self,
        error: ValidationError,
    ):
        self.errors.append(error)
        self.success = False

    def add_warning(
        self,
        warning: ValidationError,
    ):
        self.warnings.append(warning)