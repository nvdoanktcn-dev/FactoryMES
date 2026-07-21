from __future__ import annotations

from datetime import datetime

from src.database.session import get_session
from src.framework.base_service import BaseService
from src.framework.exception import (
    NotFoundError,
)
from src.models.production_assignment import (
    ProductionAssignment,
)
from src.models.production_execution import (
    ProductionExecution,
)
from src.repository.production_execution_repository import (
    ProductionExecutionRepository,
)


class ProductionExecutionService(BaseService):
    STATUS_RUNNING = "RUNNING"
    STATUS_STOPPED = "STOPPED"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"

    def __init__(
        self,
        session=None,
    ):
        super().__init__()

        self._owns_session = session is None
        self.session = session or get_session()

        self.repository = (
            ProductionExecutionRepository(
                self.session
            )
        )

    def get_all_executions(self):
        return self.repository.get_all()

    def get_execution(
        self,
        execution_id,
    ):
        return self.repository.get_by_id(
            execution_id
        )

    def get_by_assignment_id(
        self,
        assignment_id,
    ):
        return (
            self.repository
            .get_by_assignment_id(
                assignment_id
            )
        )

    def start_execution(
        self,
        assignment_id,
        start_time=None,
        remark=None,
    ):
        assignment = self._require_assignment(
            assignment_id
        )

        if assignment.status != "IN_PROGRESS":
            raise ValueError(
                (
                    "Assignment must be IN_PROGRESS "
                    "before starting execution."
                )
            )

        running = (
            self.repository
            .get_running_by_assignment_id(
                assignment.id
            )
        )

        if running is not None:
            raise ValueError(
                (
                    "A RUNNING execution already exists "
                    f"for Assignment #{assignment.id}."
                )
            )

        execution = ProductionExecution(
            assignment_id=assignment.id,
            start_time=(
                self._normalize_datetime(
                    start_time
                )
                or datetime.now()
            ),
            status=self.STATUS_RUNNING,
            remark=self._clean_optional_text(
                remark
            ),
        )

        return self.repository.add(
            execution
        )

    def stop_execution(
        self,
        execution_id,
        *,
        ok_qty=0,
        ng_qty=0,
        processing_ng_qty=0,
        blank_ng_qty=0,
        downtime_minutes=0,
        end_time=None,
        complete=False,
        remark=None,
    ):
        execution = self._require_execution(
            execution_id
        )

        if execution.status != self.STATUS_RUNNING:
            raise ValueError(
                "Only RUNNING execution can be stopped."
            )

        normalized_end = (
            self._normalize_datetime(
                end_time
            )
            or datetime.now()
        )

        if normalized_end <= execution.start_time:
            raise ValueError(
                "End Time must be after Start Time."
            )

        execution.end_time = normalized_end

        execution.ok_qty = (
            self._normalize_non_negative_int(
                ok_qty,
                "OK Qty",
            )
        )

        execution.ng_qty = (
            self._normalize_non_negative_int(
                ng_qty,
                "NG Qty",
            )
        )

        execution.processing_ng_qty = (
            self._normalize_non_negative_int(
                processing_ng_qty,
                "Processing NG Qty",
            )
        )

        execution.blank_ng_qty = (
            self._normalize_non_negative_int(
                blank_ng_qty,
                "Blank NG Qty",
            )
        )

        execution.downtime_minutes = (
            self._normalize_non_negative_float(
                downtime_minutes,
                "Downtime Minutes",
            )
        )

        total_minutes = (
            normalized_end
            - execution.start_time
        ).total_seconds() / 60.0

        execution.runtime_minutes = max(
            0.0,
            total_minutes
            - execution.downtime_minutes,
        )

        execution.status = (
            self.STATUS_COMPLETED
            if complete
            else self.STATUS_STOPPED
        )

        if remark is not None:
            execution.remark = (
                self._clean_optional_text(
                    remark
                )
            )

        self.repository.update()

        return execution

    def cancel_execution(
        self,
        execution_id,
    ):
        execution = self._require_execution(
            execution_id
        )

        if execution.status == (
            self.STATUS_COMPLETED
        ):
            raise ValueError(
                "COMPLETED execution cannot be cancelled."
            )

        execution.status = (
            self.STATUS_CANCELLED
        )

        self.repository.update()

        return execution

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        if self._owns_session:
            self.session.close()

    def _require_execution(
        self,
        execution_id,
    ):
        execution = self.get_execution(
            execution_id
        )

        if execution is None:
            raise NotFoundError(
                (
                    "Production Execution "
                    f"not found: {execution_id}"
                )
            )

        return execution

    def _require_assignment(
        self,
        assignment_id,
    ):
        assignment = (
            self.session
            .query(ProductionAssignment)
            .filter(
                ProductionAssignment.id
                == int(assignment_id)
            )
            .first()
        )

        if assignment is None:
            raise NotFoundError(
                (
                    "Production Assignment "
                    f"not found: {assignment_id}"
                )
            )

        return assignment

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
                f"Invalid datetime: {value}"
            ) from error

    @staticmethod
    def _normalize_non_negative_int(
        value,
        field_name,
    ):
        try:
            number = int(
                float(
                    value or 0
                )
            )
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid {field_name}: {value}"
            ) from error

        if number < 0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )

        return number

    @staticmethod
    def _normalize_non_negative_float(
        value,
        field_name,
    ):
        try:
            number = float(
                value or 0
            )
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid {field_name}: {value}"
            ) from error

        if number < 0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )

        return number

    @staticmethod
    def _clean_optional_text(
        value,
    ):
        text = str(
            value or ""
        ).strip()

        return text or None