from __future__ import annotations

from datetime import datetime
from math import isfinite

from src.framework.exception import NotFoundError
from src.models.production_execution import (
    ProductionExecution,
)
from src.models.production_ng import ProductionNG
from src.repository.production_ng_repository import (
    ProductionNGRepository,
)
from src.services.base_service import SessionOwnedService


class ProductionNGService(SessionOwnedService):
    TYPE_PROCESSING = "PROCESSING"
    TYPE_BLANK = "BLANK"

    VALID_TYPES = {
        TYPE_PROCESSING,
        TYPE_BLANK,
    }

    REASONS = {
        "DIMENSION": "Sai kích thước",
        "SCRATCH": "Trầy xước",
        "BURR": "Ba via",
        "APPEARANCE": "Ngoại quan",
        "DEFORMATION": "Biến dạng",
        "TOOL_DAMAGE": "Dao cụ hư hỏng",
        "PROGRAM_ERROR": "Lỗi chương trình",
        "CASTING_DEFECT": "Lỗi phôi đúc",
        "MATERIAL_DEFECT": "Lỗi vật liệu",
        "OTHER": "Khác",
    }

    def __init__(
        self,
        session=None,
    ):
        super().__init__(session=session)

        self.repository = ProductionNGRepository(
            self.session
        )

    # ==========================================================
    # Query
    # ==========================================================

    def get_all_records(self):
        return self.repository.get_all()

    def get_record(
        self,
        ng_id,
    ):
        return self.repository.get_by_id(
            ng_id
        )

    def get_by_execution_id(
        self,
        execution_id,
    ):
        return self.repository.get_by_execution_id(
            execution_id
        )

    def get_total_ng(
        self,
        execution_id,
    ) -> int:
        return (
            self.repository
            .sum_quantity_by_execution_id(
                execution_id
            )
        )

    def get_processing_ng(
        self,
        execution_id,
    ) -> int:
        return (
            self.repository
            .sum_quantity_by_execution_type(
                execution_id,
                self.TYPE_PROCESSING,
            )
        )

    def get_blank_ng(
        self,
        execution_id,
    ) -> int:
        return (
            self.repository
            .sum_quantity_by_execution_type(
                execution_id,
                self.TYPE_BLANK,
            )
        )

    # ==========================================================
    # Create
    # ==========================================================

    def record_ng(
        self,
        execution_id,
        ng_type,
        reason_code,
        quantity,
        *,
        recorded_at=None,
        employee_code=None,
        remark=None,
    ):
        execution = self._require_execution(
            execution_id
        )

        if str(
            execution.status or ""
        ).strip().upper() not in {
            "RUNNING",
            "STOPPED",
            "COMPLETED",
        }:
            raise ValueError(
                (
                    "NG can only be recorded for "
                    "RUNNING, STOPPED or COMPLETED "
                    "execution."
                )
            )

        normalized_type = (
            self._normalize_ng_type(
                ng_type
            )
        )

        normalized_reason = (
            self._normalize_reason_code(
                reason_code
            )
        )

        normalized_quantity = (
            self._normalize_positive_int(
                quantity,
                "NG Quantity",
            )
        )

        normalized_recorded_at = (
            self._normalize_datetime(
                recorded_at
            )
            or execution.end_time
            or datetime.now()
        )
        normalized_employee_code = (
            self._clean_optional_upper(
                employee_code
            )
        )

        self._validate_recorded_at(
            execution,
            normalized_recorded_at,
        )
        self._ensure_not_duplicate(
            execution_id=execution.id,
            ng_type=normalized_type,
            reason_code=normalized_reason,
            quantity=normalized_quantity,
            recorded_at=normalized_recorded_at,
            employee_code=normalized_employee_code,
        )

        record = ProductionNG(
            execution_id=execution.id,
            ng_type=normalized_type,
            reason_code=normalized_reason,
            reason_name=self.REASONS[
                normalized_reason
            ],
            quantity=normalized_quantity,
            recorded_at=normalized_recorded_at,
            employee_code=normalized_employee_code,
            remark=(
                self._clean_optional_text(
                    remark
                )
            ),
            status="ACTIVE",
        )

        record = self.repository.add(
            record
        )

        self.require_session().flush()

        self._synchronize_execution_ng(
            execution.id
        )

        return record

    # ==========================================================
    # Update
    # ==========================================================

    def update_ng(
        self,
        ng_id,
        *,
        ng_type,
        reason_code,
        quantity,
        recorded_at=None,
        employee_code=None,
        remark=None,
    ):
        record = self._require_record(
            ng_id
        )

        if record.status != "ACTIVE":
            raise ValueError(
                "Only ACTIVE NG record can be edited."
            )

        execution = self._require_execution(
            record.execution_id
        )
        if str(
            execution.status or ""
        ).strip().upper() not in {
            "RUNNING",
            "STOPPED",
            "COMPLETED",
        }:
            raise ValueError(
                (
                    "NG can only be edited for "
                    "RUNNING, STOPPED or COMPLETED "
                    "execution."
                )
            )
        normalized_type = (
            self._normalize_ng_type(
                ng_type
            )
        )

        normalized_reason = (
            self._normalize_reason_code(
                reason_code
            )
        )

        normalized_quantity = (
            self._normalize_positive_int(
                quantity,
                "NG Quantity",
            )
        )

        normalized_recorded_at = record.recorded_at
        if recorded_at is not None:
            normalized_recorded_at = (
                self._normalize_datetime(
                    recorded_at
                )
            )

        normalized_employee_code = (
            self._clean_optional_upper(
                employee_code
            )
        )
        self._validate_recorded_at(
            execution,
            normalized_recorded_at,
        )
        self._ensure_not_duplicate(
            execution_id=record.execution_id,
            ng_type=normalized_type,
            reason_code=normalized_reason,
            quantity=normalized_quantity,
            recorded_at=normalized_recorded_at,
            employee_code=normalized_employee_code,
            exclude_ng_id=record.id,
        )

        record.ng_type = normalized_type
        record.reason_code = normalized_reason
        record.reason_name = self.REASONS[
            normalized_reason
        ]
        record.quantity = normalized_quantity
        record.recorded_at = normalized_recorded_at
        record.employee_code = normalized_employee_code
        record.remark = (
            self._clean_optional_text(
                remark
            )
        )

        self.repository.update()

        self._synchronize_execution_ng(
            record.execution_id
        )

        return record

    # ==========================================================
    # Cancel
    # ==========================================================

    def cancel_ng(
        self,
        ng_id,
    ):
        record = self._require_record(
            ng_id
        )

        if record.status != "ACTIVE":
            raise ValueError(
                "Only ACTIVE NG record can be cancelled."
            )

        record.status = "CANCELLED"

        self.repository.update()

        self._synchronize_execution_ng(
            record.execution_id
        )

        return record

    # ==========================================================
    # Synchronization
    # ==========================================================

    def _synchronize_execution_ng(
        self,
        execution_id,
    ):
        execution = self._require_execution(
            execution_id
        )

        execution.processing_ng_qty = (
            self.get_processing_ng(
                execution_id
            )
        )

        execution.blank_ng_qty = (
            self.get_blank_ng(
                execution_id
            )
        )

        execution.ng_qty = (
            execution.processing_ng_qty
            + execution.blank_ng_qty
        )

        self.require_session().flush()

    # ==========================================================
    # Validation
    # ==========================================================

    def _require_record(
        self,
        ng_id,
    ):
        record = self.get_record(
            ng_id
        )

        if record is None:
            raise NotFoundError(
                f"Production NG not found: {ng_id}"
            )

        return record

    def _require_execution(
        self,
        execution_id,
    ):
        try:
            normalized_id = int(
                execution_id
            )
        except (TypeError, ValueError) as error:
            raise ValueError(
                (
                    "Invalid Execution ID: "
                    f"{execution_id}"
                )
            ) from error

        execution = (
            self.require_session()
            .query(ProductionExecution)
            .filter(
                ProductionExecution.id
                == normalized_id
            )
            .first()
        )

        if execution is None:
            raise NotFoundError(
                (
                    "Production Execution "
                    f"not found: {normalized_id}"
                )
            )

        return execution

    @staticmethod
    def _validate_recorded_at(
        execution,
        recorded_at,
    ):
        if recorded_at < execution.start_time:
            raise ValueError(
                (
                    "NG Recorded At cannot be before "
                    "Execution Start Time."
                )
            )

        if (
            execution.end_time is not None
            and recorded_at > execution.end_time
        ):
            raise ValueError(
                (
                    "NG Recorded At cannot be after "
                    "Execution End Time."
                )
            )

    def _ensure_not_duplicate(
        self,
        *,
        execution_id,
        ng_type,
        reason_code,
        quantity,
        recorded_at,
        employee_code,
        exclude_ng_id=None,
    ):
        duplicate = self.repository.find_duplicate(
            execution_id=execution_id,
            ng_type=ng_type,
            reason_code=reason_code,
            quantity=quantity,
            recorded_at=recorded_at,
            employee_code=employee_code,
            exclude_ng_id=exclude_ng_id,
        )
        if duplicate is not None:
            raise ValueError(
                (
                    "Duplicate Production NG record: "
                    f"#{duplicate.id}."
                )
            )

    @classmethod
    def _normalize_ng_type(
        cls,
        value,
    ):
        normalized = str(
            value or ""
        ).strip().upper()

        if normalized not in cls.VALID_TYPES:
            raise ValueError(
                f"Invalid NG Type: {normalized}"
            )

        return normalized

    @classmethod
    def _normalize_reason_code(
        cls,
        value,
    ):
        normalized = str(
            value or ""
        ).strip().upper()

        if normalized not in cls.REASONS:
            raise ValueError(
                (
                    "Invalid NG Reason: "
                    f"{normalized}"
                )
            )

        return normalized

    @staticmethod
    def _normalize_positive_int(
        value,
        field_name,
    ):
        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid {field_name}: {value}"
            ) from error

        if not isfinite(numeric_value) or not numeric_value.is_integer():
            raise ValueError(
                f"{field_name} must be a whole number."
            )

        number = int(numeric_value)
        if number <= 0:
            raise ValueError(
                (
                    f"{field_name} must be "
                    "greater than zero."
                )
            )

        return number

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
            return datetime.fromisoformat(
                text
            )
        except ValueError as error:
            raise ValueError(
                (
                    "Invalid datetime value: "
                    f"{value}"
                )
            ) from error

    @staticmethod
    def _clean_optional_upper(
        value,
    ):
        text = str(
            value or ""
        ).strip().upper()

        return text or None

    @staticmethod
    def _clean_optional_text(
        value,
    ):
        text = str(
            value or ""
        ).strip()

        return text or None

    # ==========================================================
    # Transaction
    # ==========================================================

    def commit(self):
        self.require_session().commit()

    def rollback(self):
        self.require_session().rollback()

    def commit_changes(self):
        self.commit()

    def rollback_changes(self):
        self.rollback()
