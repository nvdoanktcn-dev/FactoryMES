from src.engine.production.production_calculator import (
    ProductionCalculator,
)
from src.engine.production.production_engine_result import (
    ProductionEngineResult,
)
from src.engine.production.production_validator import (
    ProductionValidator,
)
from src.engine.production.production_warning import (
    ProductionWarningEngine,
)


class ProductionEngine:
    """
    Engine điều phối Production Execution.

    Luồng:

        Raw Production Entry
            ↓
        ProductionValidator
            ↓
        ProductionCalculator
            ↓
        ProductionWarningEngine
            ↓
        ProductionEngineResult

    Engine không truy cập database.
    """

    def __init__(
        self,
        validator=None,
        calculator=None,
        warning_engine=None,
    ):
        self.validator = (
            validator
            or ProductionValidator()
        )

        self.calculator = (
            calculator
            or ProductionCalculator()
        )

        self.warning_engine = (
            warning_engine
            or ProductionWarningEngine()
        )

    def process(
        self,
        data,
        work_order=None,
        routing=None,
        machine=None,
        existing_record_hashes=None,
        standard_cycle_time_sec=None,
    ):
        """
        Kiểm tra, tính toán và tạo cảnh báo.

        Args:
            data:
                Dictionary Production Entry.

            work_order:
                WorkOrder object.

            routing:
                Routing object của Product + OP.

            machine:
                Machine object.

            existing_record_hashes:
                Set hash dùng kiểm tra trùng.

            standard_cycle_time_sec:
                Có thể truyền trực tiếp thay vì
                dùng routing.cycle_time_sec.

        Returns:
            ProductionEngineResult
        """

        validation = self.validator.validate(
            data=data,
            work_order=work_order,
            routing=routing,
            machine=machine,
            existing_record_hashes=(
                existing_record_hashes
                or set()
            ),
        )

        normalized_data = dict(
            validation.normalized_data
        )

        if not validation.is_valid:
            return ProductionEngineResult(
                validation=validation,
                calculation=None,
                warning_result=None,
                normalized_data=normalized_data,
            )

        calculation = self.calculator.calculate(
            data=normalized_data,
            routing=routing,
            standard_cycle_time_sec=(
                standard_cycle_time_sec
            ),
        )

        warning_result = (
            self.warning_engine.evaluate(
                calculation
            )
        )

        return ProductionEngineResult(
            validation=validation,
            calculation=calculation,
            warning_result=warning_result,
            normalized_data=normalized_data,
        )

    def validate_only(
        self,
        data,
        work_order=None,
        routing=None,
        machine=None,
        existing_record_hashes=None,
    ):
        """
        Chỉ chạy Validator, không tính KPI.
        """
        return self.validator.validate(
            data=data,
            work_order=work_order,
            routing=routing,
            machine=machine,
            existing_record_hashes=(
                existing_record_hashes
                or set()
            ),
        )

    def calculate_only(
        self,
        normalized_data,
        routing=None,
        standard_cycle_time_sec=None,
    ):
        """
        Chỉ chạy Calculator với dữ liệu đã chuẩn hóa.
        """
        return self.calculator.calculate(
            data=normalized_data,
            routing=routing,
            standard_cycle_time_sec=(
                standard_cycle_time_sec
            ),
        )