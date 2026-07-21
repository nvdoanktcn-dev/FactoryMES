from __future__ import annotations

from datetime import datetime

from src.database.session import get_session
from src.framework.base_service import BaseService
from src.framework.exception import (
    NotFoundError,
)
from src.models.production_downtime import (
    ProductionDowntime,
)
from src.models.production_execution import (
    ProductionExecution,
)
from src.repository.production_downtime_repository import (
    ProductionDowntimeRepository,
)


class ProductionDowntimeService(
    BaseService
):
    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"
    STATUS_CANCELLED = "CANCELLED"

    REASONS = {
        "WAIT_OPERATOR": "Chờ người",
        "WAIT_MATERIAL": "Chờ liệu",
        "WAIT_ORDER": "Chờ đơn",
        "MAINTENANCE": "Bảo dưỡng máy móc",
        "POWER_OUTAGE": "Mất điện",
        "MACHINE_REPAIR": "Sửa chữa máy móc",
        "TOOL_CHANGE": "Thay dao/khuôn",
        "PRODUCT_PROGRAMMING": (
            "Lập trình cho sản phẩm"
        ),
    }

    def __init__(
        self,
        session=None,
    ):
        super().__init__()

        self._owns_session = (
            session is None
        )

        self.session = (
            session
            or get_session()
        )

        self.repository = (
            ProductionDowntimeRepository(
                self.session
            )
        )

    # ==========================================================
    # Query
    # ==========================================================

    def get_all_events(self):
        return self.repository.get_all()

    def get_event(
        self,
        downtime_id,
    ):
        return self.repository.get_by_id(
            downtime_id
        )

    def get_by_execution_id(
        self,
        execution_id,
    ):
        return (
            self.repository
            .get_by_execution_id(
                execution_id
            )
        )

    def get_open_events(self):
        return self.repository.get_open_events()

    def get_total_minutes(
        self,
        execution_id,
    ) -> float:
        return (
            self.repository
            .sum_duration_by_execution_id(
                execution_id
            )
        )

    # ==========================================================
    # Start downtime
    # ==========================================================

    def start_downtime(
        self,
        execution_id,
        reason_code,
        *,
        start_time=None,
        remark=None,
    ):
        execution = self._require_execution(
            execution_id
        )

        if str(
            execution.status or ""
        ).upper() != "RUNNING":
            raise ValueError(
                (
                    "Downtime can only be started "
                    "for a RUNNING execution."
                )
            )

        existing = (
            self.repository
            .get_open_by_execution_id(
                execution.id
            )
        )

        if existing is not None:
            raise ValueError(
                (
                    "An OPEN downtime event already "
                    "exists for this execution: "
                    f"#{existing.id}"
                )
            )

        normalized_reason = (
            self._normalize_reason_code(
                reason_code
            )
        )

        event = ProductionDowntime(
            execution_id=execution.id,
            reason_code=normalized_reason,
            reason_name=self.REASONS[
                normalized_reason
            ],
            start_time=(
                self._normalize_datetime(
                    start_time
                )
                or datetime.now()
            ),
            status=self.STATUS_OPEN,
            remark=self._clean_optional_text(
                remark
            ),
        )

        return self.repository.add(
            event
        )

    # ==========================================================
    # Stop downtime
    # ==========================================================

    def stop_downtime(
        self,
        downtime_id,
        *,
        end_time=None,
        remark=None,
    ):
        event = self._require_event(
            downtime_id
        )

        if event.status != self.STATUS_OPEN:
            raise ValueError(
                (
                    "Only OPEN downtime event "
                    "can be stopped."
                )
            )

        normalized_end = (
            self._normalize_datetime(
                end_time
            )
            or datetime.now()
        )

        if normalized_end <= event.start_time:
            raise ValueError(
                (
                    "Downtime End Time must be "
                    "after Start Time."
                )
            )

        event.end_time = normalized_end

        event.duration_minutes = (
            normalized_end
            - event.start_time
        ).total_seconds() / 60.0

        event.status = self.STATUS_CLOSED

        if remark is not None:
            event.remark = (
                self._clean_optional_text(
                    remark
                )
            )

        self.repository.update()

        self._synchronize_execution_downtime(
            event.execution_id
        )

        return event

    # ==========================================================
    # Cancel
    # ==========================================================

    def cancel_downtime(
        self,
        downtime_id,
    ):
        event = self._require_event(
            downtime_id
        )

        if event.status == self.STATUS_CLOSED:
            raise ValueError(
                (
                    "CLOSED downtime event "
                    "cannot be cancelled."
                )
            )

        event.status = self.STATUS_CANCELLED
        event.end_time = datetime.now()
        event.duration_minutes = 0.0

        self.repository.update()

        return event

    # ==========================================================
    # Synchronization
    # ==========================================================

    def _synchronize_execution_downtime(
        self,
        execution_id,
    ):
        execution = self._require_execution(
            execution_id
        )

        execution.downtime_minutes = (
            self.get_total_minutes(
                execution_id
            )
        )

        if execution.end_time is not None:
            elapsed_minutes = (
                execution.end_time
                - execution.start_time
            ).total_seconds() / 60.0

            execution.runtime_minutes = max(
                0.0,
                elapsed_minutes
                - execution.downtime_minutes,
            )

        self.session.flush()

    # ==========================================================
    # Validation
    # ==========================================================

    def _require_event(
        self,
        downtime_id,
    ):
        event = self.get_event(
            downtime_id
        )

        if event is None:
            raise NotFoundError(
                (
                    "Production Downtime "
                    f"not found: {downtime_id}"
                )
            )

        return event

    def _require_execution(
        self,
        execution_id,
    ):
        try:
            normalized_id = int(
                execution_id
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                (
                    "Invalid Execution ID: "
                    f"{execution_id}"
                )
            ) from error

        execution = (
            self.session
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

    @classmethod
    def _normalize_reason_code(
        cls,
        value,
    ):
        code = str(
            value or ""
        ).strip().upper()

        if code not in cls.REASONS:
            raise ValueError(
                (
                    "Invalid Downtime Reason: "
                    f"{code}"
                )
            )

        return code

    @staticmethod
    def _normalize_datetime(
        value,
    ):
        if value is None or value == "":
            return None

        if isinstance(
            value,
            datetime,
        ):
            return value

        text = str(
            value
        ).strip()

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
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        if self._owns_session:
            self.session.close()