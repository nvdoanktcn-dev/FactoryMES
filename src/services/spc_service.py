from __future__ import annotations

from datetime import datetime

from src.framework.exception import ValidationError
from src.models.quality_measurement import QualityMeasurement
from src.repository.quality_measurement_repository import (
    QualityMeasurementRepository,
)
from src.services.base_service import SessionOwnedService
from src.spc.exceptions import InsufficientDataError
from src.spc.models import SPCAnalysisResult
from src.spc.spc_engine import SPCEngine


class SPCService(SessionOwnedService):
    """
    Giai đoạn 6 (Quality, 2026-07-25): facade nối `SPCEngine` (thuần,
    không phụ thuộc DB - xem `src/spc/spc_engine.py`) với dữ liệu đo
    lường thật (`QualityMeasurement`), theo đúng kiến trúc đã dùng ở
    Giai đoạn 5 (`ProductionPlanningService` nối `CapacityEngine`/
    `SchedulerEngine` thuần với dữ liệu Work Order/Routing/Machine
    thật).
    """

    DEFAULT_HISTORY_LIMIT = 50

    def __init__(
        self,
        session=None,
        engine=None,
    ):
        super().__init__(session=session)

        self.repository = QualityMeasurementRepository(
            self.session
        )

        self.engine = engine or SPCEngine

    # ==========================================================
    # Query (cho combo box UI)
    # ==========================================================

    def list_product_codes(self):
        return self.repository.get_distinct_product_codes()

    def list_characteristics(
        self,
        product_code=None,
    ):
        rows = self.repository.get_distinct_characteristics(
            product_code
        )

        return [
            {
                "product_code": row[0],
                "characteristic_name": row[1],
            }
            for row in rows
        ]

    def get_measurements(
        self,
        product_code,
        characteristic_name,
        limit=None,
    ):
        return self.repository.get_by_characteristic(
            product_code,
            characteristic_name,
            limit=limit,
        )

    # ==========================================================
    # Record a new measurement
    # ==========================================================

    def record_measurement(
        self,
        data,
    ):
        measurement = QualityMeasurement(
            product_code=self._require_text(
                data.get("product_code"),
                "Product Code",
            ).upper(),
            characteristic_name=self._require_text(
                data.get("characteristic_name"),
                "Characteristic Name",
            ),
            measured_value=self._require_float(
                data.get("measured_value"),
                "Measured Value",
            ),
            unit=self._clean_optional_text(
                data.get("unit")
            ),
            target_value=self._optional_float(
                data.get("target_value")
            ),
            usl=self._optional_float(
                data.get("usl")
            ),
            lsl=self._optional_float(
                data.get("lsl")
            ),
            work_order_no=self._clean_optional_upper(
                data.get("work_order_no")
            ),
            machine_code=self._clean_optional_upper(
                data.get("machine_code")
            ),
            employee_code=self._clean_optional_upper(
                data.get("employee_code")
            ),
            measured_at=(
                self._normalize_datetime(
                    data.get("measured_at")
                )
                or datetime.now()
            ),
            remark=self._clean_optional_text(
                data.get("remark")
            ),
        )

        if (
            measurement.usl is not None
            and measurement.lsl is not None
            and measurement.usl <= measurement.lsl
        ):
            raise ValidationError(
                "USL must be greater than LSL."
            )

        self.repository.add(measurement)

        self.commit()

        return measurement

    # ==========================================================
    # Analyze
    # ==========================================================

    def analyze(
        self,
        product_code,
        characteristic_name,
        *,
        limit=None,
    ) -> SPCAnalysisResult:
        measurements = self.get_measurements(
            product_code,
            characteristic_name,
            limit=(
                limit
                if limit is not None
                else self.DEFAULT_HISTORY_LIMIT
            ),
        )

        if not measurements:
            raise InsufficientDataError(
                "No measurements recorded for "
                f"{product_code} / {characteristic_name}."
            )

        values = [m.measured_value for m in measurements]

        latest = measurements[-1]

        points, statistics_result = self.engine.analyze(
            values,
            usl=latest.usl,
            lsl=latest.lsl,
        )

        return SPCAnalysisResult(
            product_code=product_code,
            characteristic_name=characteristic_name,
            points=points,
            statistics=statistics_result,
        )

    # ==========================================================
    # Validation helpers
    # ==========================================================

    @staticmethod
    def _require_text(
        value,
        field_name,
    ):
        text = str(value or "").strip()

        if not text:
            raise ValidationError(
                f"{field_name} is required."
            )

        return text

    @staticmethod
    def _require_float(
        value,
        field_name,
    ):
        try:
            return float(value)
        except (TypeError, ValueError) as error:
            raise ValidationError(
                f"Invalid {field_name}: {value}"
            ) from error

    @staticmethod
    def _optional_float(
        value,
    ):
        if value is None or value == "":
            return None

        try:
            return float(value)
        except (TypeError, ValueError) as error:
            raise ValidationError(
                f"Invalid numeric value: {value}"
            ) from error

    @staticmethod
    def _clean_optional_text(
        value,
    ):
        text = str(value or "").strip()

        return text or None

    @staticmethod
    def _clean_optional_upper(
        value,
    ):
        text = str(value or "").strip().upper()

        return text or None

    @staticmethod
    def _normalize_datetime(
        value,
    ):
        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            return value

        text = str(value).strip()

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d/%m/%Y %H:%M",
        ]

        for date_format in formats:
            try:
                return datetime.strptime(
                    text,
                    date_format,
                )
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(text)
        except ValueError as error:
            raise ValidationError(
                f"Invalid datetime value: {value}"
            ) from error
