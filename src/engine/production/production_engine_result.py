from dataclasses import dataclass
from typing import Any

from src.engine.production.dto import (
    ProductionValidationResult,
)
from src.engine.production.production_calculation_result import (
    ProductionCalculationResult,
)
from src.engine.production.production_warning import (
    ProductionWarningResult,
)


@dataclass(slots=True)
class ProductionEngineResult:
    """
    Kết quả cuối cùng của ProductionEngine.
    """

    validation: ProductionValidationResult

    calculation: (
        ProductionCalculationResult
        | None
    )

    warning_result: (
        ProductionWarningResult
        | None
    )

    normalized_data: dict[str, Any]

    @property
    def is_valid(self):
        return self.validation.is_valid

    @property
    def errors(self):
        return self.validation.errors

    @property
    def warnings(self):
        warnings = list(
            self.validation.warnings
        )

        if self.warning_result is not None:
            warnings.extend(
                self.warning_result.warnings
            )

        return warnings

    @property
    def has_warnings(self):
        return len(self.warnings) > 0

    @property
    def can_save(self):
        """
        Chỉ cho phép lưu khi không có Validation Error.
        Warning không chặn lưu.
        """
        return self.is_valid