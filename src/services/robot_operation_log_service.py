from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session

from src.framework.exception import NotFoundError, ValidationError
from src.framework.validator import BaseValidator
from src.models.robot_operation_log import RobotOperationLog
from src.repository.robot_operation_log_repository import (
    RobotOperationLogRepository,
)
from src.repository.robot_repository import RobotRepository
from src.services.base_service import SessionOwnedService


class RobotOperationLogService(SessionOwnedService):
    """
    Service quản lý log vận hành Robot (thời gian chạy, sản lượng, lỗi).
    """

    VALID_STATUS = {
        "COMPLETED",
        "RUNNING",
        "ERROR",
        "STOPPED",
    }

    def __init__(
        self,
        session: Session | None = None,
        repository: RobotOperationLogRepository | None = None,
    ) -> None:
        if repository is not None:
            super().__init__(
                session=getattr(repository, "session", None)
            )
            self._owns_session = False
            self.repository = repository
            self.robot_repository = RobotRepository(self.session)
            return

        super().__init__(session=session)

        self.repository = RobotOperationLogRepository(
            self.require_session()
        )

        self.robot_repository = RobotRepository(
            self.require_session()
        )

    # ==========================================================
    # Query
    # ==========================================================

    def get_all_logs(self):
        return self.repository.get_all()

    def get_log(self, log_id):
        return self.repository.get_by_id(log_id)

    def search_logs(self, keyword):
        logs = self.get_all_logs()

        text = str(keyword or "").strip().lower()

        if not text:
            return logs

        return [
            log
            for log in logs
            if (
                text in str(log.robot_code or "").lower()
                or text in str(log.shift or "").lower()
                or text in str(log.error_code or "").lower()
                or text in str(log.error_message or "").lower()
                or text in str(log.status or "").lower()
            )
        ]

    # ==========================================================
    # Create
    # ==========================================================

    def create_log(self, data):
        normalized = self._normalize_data(data)

        self._validate_log(normalized)

        log = RobotOperationLog(**normalized)

        self.log_info(
            f"Create Robot Operation Log: {normalized['robot_code']}"
        )

        return self.repository.add(log)

    # ==========================================================
    # Update
    # ==========================================================

    def update_log(self, log_id, data):
        log = self.repository.get_by_id(log_id)

        if log is None:
            raise NotFoundError(
                f"Robot Operation Log not found: {log_id}"
            )

        normalized = self._normalize_data(data)

        self._validate_log(normalized)

        for field, value in normalized.items():
            setattr(log, field, value)

        self.log_info(
            f"Update Robot Operation Log: {log_id}"
        )

        self.repository.update()

        return log

    # ==========================================================
    # Delete
    # ==========================================================

    def delete_log(self, log_id):
        log = self.repository.get_by_id(log_id)

        if log is None:
            raise NotFoundError(
                f"Robot Operation Log not found: {log_id}"
            )

        self.log_warning(
            f"Delete Robot Operation Log: {log_id}"
        )

        return self.repository.delete(log)

    # ==========================================================
    # Validation and normalization
    # ==========================================================

    def _validate_log(self, normalized):
        BaseValidator.required(
            normalized["robot_code"], "Robot Code"
        )

        if not self.robot_repository.exists(
            normalized["robot_code"]
        ):
            raise ValidationError(
                "Robot Code does not exist in Robot catalog: "
                f"{normalized['robot_code']}"
            )

        if normalized["status"] not in self.VALID_STATUS:
            raise ValidationError(
                f"Invalid status: {normalized['status']}"
            )

    @classmethod
    def _normalize_data(cls, data):
        data = dict(data or {})

        return {
            "robot_code": str(
                data.get("robot_code") or ""
            ).strip().upper(),
            "log_date": cls._parse_date(
                data.get("log_date")
            ),
            "shift": cls._clean_optional_text(
                data.get("shift")
            ),
            "start_time": cls._parse_datetime(
                data.get("start_time")
            ),
            "end_time": cls._parse_datetime(
                data.get("end_time")
            ),
            "output_qty": cls._parse_float(
                data.get("output_qty")
            ),
            "ng_qty": cls._parse_float(
                data.get("ng_qty")
            ),
            "error_code": cls._clean_optional_text(
                data.get("error_code")
            ),
            "error_message": cls._clean_optional_text(
                data.get("error_message")
            ),
            "status": str(
                data.get("status") or "COMPLETED"
            ).strip().upper(),
            "remark": cls._clean_optional_text(
                data.get("remark")
            ),
        }

    @staticmethod
    def _clean_optional_text(value):
        text = str(value or "").strip()
        return text or None

    @staticmethod
    def _parse_float(value):
        if value in (None, ""):
            return 0.0

        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _parse_date(value):
        if value in (None, ""):
            return None

        if isinstance(value, date) and not isinstance(
            value, datetime
        ):
            return value

        if isinstance(value, datetime):
            return value.date()

        try:
            return datetime.strptime(
                str(value)[:10], "%Y-%m-%d"
            ).date()
        except ValueError:
            return None

    @staticmethod
    def _parse_datetime(value):
        if value in (None, ""):
            return None

        if isinstance(value, datetime):
            return value

        text = str(value).strip()

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue

        return None
