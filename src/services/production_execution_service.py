from __future__ import annotations

from datetime import datetime
from math import isfinite

from src.framework.exception import NotFoundError
from src.models.production_assignment import ProductionAssignment
from src.models.production_execution import ProductionExecution
from src.repository.production_execution_repository import ProductionExecutionRepository
from src.services.base_service import SessionOwnedService


class ProductionExecutionService(SessionOwnedService):
    STATUS_RUNNING = "RUNNING"
    STATUS_STOPPED = "STOPPED"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"

    def __init__(self, session=None):
        super().__init__(session=session)
        self.repository = ProductionExecutionRepository(self.session)

    def get_all_executions(self):
        return self.repository.get_all()

    def get_execution(self, execution_id):
        return self.repository.get_by_id(execution_id)

    def get_by_assignment_id(self, assignment_id):
        return self.repository.get_by_assignment_id(assignment_id)

    def start_execution(self, assignment_id, start_time=None, remark=None):
        assignment = self._require_assignment(assignment_id)

        if assignment.status != "IN_PROGRESS":
            raise ValueError(
                "Assignment must be IN_PROGRESS before starting execution."
            )

        running = self.repository.get_running_by_assignment_id(assignment.id)
        if running is not None:
            raise ValueError(
                "A RUNNING execution already exists "
                f"for Assignment #{assignment.id}."
            )

        normalized_start = (
            self._normalize_datetime(start_time)
            or datetime.now()
        )

        latest = self.repository.get_latest_by_assignment_id(
            assignment.id
        )
        if (
            latest is not None
            and latest.end_time is not None
            and normalized_start < latest.end_time
        ):
            raise ValueError(
                (
                    "Execution Start Time overlaps "
                    f"Execution #{latest.id}; it must be "
                    f"on or after {latest.end_time:%Y-%m-%d %H:%M:%S}."
                )
            )

        execution = ProductionExecution(
            assignment_id=assignment.id,
            start_time=normalized_start,
            status=self.STATUS_RUNNING,
            remark=self._clean_optional_text(remark),
        )
        return self.repository.add(execution)

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
        execution = self._require_execution(execution_id)

        if execution.status != self.STATUS_RUNNING:
            raise ValueError("Only RUNNING execution can be stopped.")

        normalized_end = self._normalize_datetime(end_time) or datetime.now()
        if normalized_end <= execution.start_time:
            raise ValueError("End Time must be after Start Time.")

        normalized_ok_qty = self._normalize_non_negative_int(ok_qty, "OK Qty")
        normalized_ng_qty = self._normalize_non_negative_int(ng_qty, "NG Qty")
        normalized_processing_ng_qty = self._normalize_non_negative_int(
            processing_ng_qty, "Processing NG Qty"
        )
        normalized_blank_ng_qty = self._normalize_non_negative_int(
            blank_ng_qty, "Blank NG Qty"
        )
        normalized_downtime = self._normalize_non_negative_float(
            downtime_minutes, "Downtime Minutes"
        )

        if (
            normalized_processing_ng_qty + normalized_blank_ng_qty
            != normalized_ng_qty
        ):
            raise ValueError(
                "Processing NG Qty + Blank NG Qty must equal NG Qty."
            )

        total_minutes = (
            normalized_end - execution.start_time
        ).total_seconds() / 60.0

        if normalized_downtime > total_minutes:
            raise ValueError(
                "Downtime Minutes cannot exceed elapsed time."
            )

        execution.end_time = normalized_end
        execution.ok_qty = normalized_ok_qty
        execution.ng_qty = normalized_ng_qty
        execution.processing_ng_qty = normalized_processing_ng_qty
        execution.blank_ng_qty = normalized_blank_ng_qty
        execution.downtime_minutes = normalized_downtime
        execution.runtime_minutes = total_minutes - normalized_downtime
        execution.status = (
            self.STATUS_COMPLETED if complete else self.STATUS_STOPPED
        )

        if remark is not None:
            execution.remark = self._clean_optional_text(remark)

        self.repository.update()
        return execution

    def cancel_execution(self, execution_id):
        execution = self._require_execution(execution_id)

        if execution.status == self.STATUS_COMPLETED:
            raise ValueError("COMPLETED execution cannot be cancelled.")

        if execution.status == self.STATUS_CANCELLED:
            raise ValueError("Execution is already CANCELLED.")

        execution.status = self.STATUS_CANCELLED
        self.repository.update()
        return execution


    def aggregate_assignment_quantities(self, assignment_id):
        """Aggregate finalized execution quantities for one assignment.

        Only STOPPED and COMPLETED executions contribute to the totals.
        RUNNING and CANCELLED executions are deliberately excluded.
        """
        assignment = self._require_assignment(assignment_id)

        finalized_statuses = {
            self.STATUS_STOPPED,
            self.STATUS_COMPLETED,
        }

        executions = self.repository.get_by_assignment_id(
            assignment.id
        )

        finalized = [
            execution
            for execution in executions
            if execution.status in finalized_statuses
        ]

        return {
            "assignment_id": assignment.id,
            "execution_count": len(finalized),
            "ok_qty": sum(
                int(execution.ok_qty or 0)
                for execution in finalized
            ),
            "ng_qty": sum(
                int(execution.ng_qty or 0)
                for execution in finalized
            ),
            "processing_ng_qty": sum(
                int(execution.processing_ng_qty or 0)
                for execution in finalized
            ),
            "blank_ng_qty": sum(
                int(execution.blank_ng_qty or 0)
                for execution in finalized
            ),
            "runtime_minutes": sum(
                float(execution.runtime_minutes or 0)
                for execution in finalized
            ),
            "downtime_minutes": sum(
                float(execution.downtime_minutes or 0)
                for execution in finalized
            ),
        }

    def commit(self):
        self.require_session().commit()

    def rollback(self):
        self.require_session().rollback()

    def commit_changes(self):
        self.commit()

    def rollback_changes(self):
        self.rollback()

    def _require_execution(self, execution_id):
        execution = self.get_execution(execution_id)
        if execution is None:
            raise NotFoundError(
                f"Production Execution not found: {execution_id}"
            )
        return execution

    def _require_assignment(self, assignment_id):
        try:
            normalized_id = int(assignment_id)
        except (TypeError, ValueError) as error:
            raise NotFoundError(
                f"Production Assignment not found: {assignment_id}"
            ) from error

        assignment = (
            self.require_session().query(ProductionAssignment)
            .filter(ProductionAssignment.id == normalized_id)
            .first()
        )
        if assignment is None:
            raise NotFoundError(
                f"Production Assignment not found: {assignment_id}"
            )
        return assignment

    @staticmethod
    def _normalize_datetime(value):
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
                return datetime.strptime(text, date_format)
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(text)
        except ValueError as error:
            raise ValueError(f"Invalid datetime: {value}") from error

    @staticmethod
    def _normalize_non_negative_int(value, field_name):
        try:
            numeric_value = float(value or 0)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid {field_name}: {value}"
            ) from error

        if not isfinite(numeric_value) or not numeric_value.is_integer():
            raise ValueError(
                f"{field_name} must be a whole number."
            )

        number = int(numeric_value)
        if number < 0:
            raise ValueError(f"{field_name} cannot be negative.")
        return number

    @staticmethod
    def _normalize_non_negative_float(value, field_name):
        try:
            number = float(value or 0)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid {field_name}: {value}"
            ) from error

        if not isfinite(number):
            raise ValueError(
                f"{field_name} must be a finite number."
            )

        if number < 0:
            raise ValueError(f"{field_name} cannot be negative.")
        return number

    @staticmethod
    def _clean_optional_text(value):
        text = str(value or "").strip()
        return text or None
