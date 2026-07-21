from dataclasses import dataclass

from src.engine.production.production_engine_result import (
    ProductionEngineResult,
)


@dataclass(slots=True)
class ProductionExecutionResult:
    """
    Kết quả xử lý và lưu một Production Entry.
    """

    engine_result: ProductionEngineResult
    production_log: object | None
    progress_result: object | None
    saved: bool

    @property
    def is_valid(self):
        return self.engine_result.is_valid

    @property
    def errors(self):
        return self.engine_result.errors

    @property
    def warnings(self):
        return self.engine_result.warnings