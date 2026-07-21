from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProductionValidationIssue:
    """
    Một lỗi hoặc cảnh báo khi kiểm tra dữ liệu sản xuất.
    """

    code: str
    message: str
    field: str = ""
    severity: str = "ERROR"

    @property
    def is_error(self):
        return self.severity == "ERROR"

    @property
    def is_warning(self):
        return self.severity == "WARNING"


@dataclass(slots=True)
class ProductionValidationResult:
    """
    Kết quả kiểm tra Production Entry.
    """

    issues: list[ProductionValidationIssue] = field(
        default_factory=list
    )

    normalized_data: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def errors(self):
        return [
            issue
            for issue in self.issues
            if issue.is_error
        ]

    @property
    def warnings(self):
        return [
            issue
            for issue in self.issues
            if issue.is_warning
        ]

    @property
    def is_valid(self):
        return len(self.errors) == 0

    def add_error(
        self,
        code,
        message,
        field="",
    ):
        self.issues.append(
            ProductionValidationIssue(
                code=code,
                message=message,
                field=field,
                severity="ERROR",
            )
        )

    def add_warning(
        self,
        code,
        message,
        field="",
    ):
        self.issues.append(
            ProductionValidationIssue(
                code=code,
                message=message,
                field=field,
                severity="WARNING",
            )
        )