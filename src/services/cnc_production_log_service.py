from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session

from src.framework.exception import NotFoundError, ValidationError
from src.framework.validator import BaseValidator
from src.models.cnc_production_log import CNCProductionLog
from src.repository.cnc_production_log_repository import (
    CNCProductionLogRepository,
)
from src.services.base_service import SessionOwnedService


class CNCProductionLogService(SessionOwnedService):
    """
    Service quản lý log sản xuất CNC.

    Dữ liệu chủ yếu được nạp qua CNCImporter (từ file Excel/CSV),
    nhưng cũng hỗ trợ Add/Edit/Delete thủ công để sửa sai sót.
    """

    def __init__(
        self,
        session: Session | None = None,
        repository: CNCProductionLogRepository | None = None,
    ) -> None:
        if repository is not None:
            super().__init__(
                session=getattr(repository, "session", None)
            )
            self._owns_session = False
            self.repository = repository
            return

        super().__init__(session=session)

        self.repository = CNCProductionLogRepository(
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
                text in str(log.machine_name or "").lower()
                or text in str(log.work_order_no or "").lower()
                or text in str(log.product_name or "").lower()
                or text in str(log.operator_name or "").lower()
                or text in str(log.operation or "").lower()
                or text in str(log.shift or "").lower()
            )
        ]

    # ==========================================================
    # Create (dùng chung cho import và nhập tay)
    # ==========================================================

    def create_log(self, data):
        normalized = self._normalize_data(data)

        self._validate_log(normalized)

        log = CNCProductionLog(**normalized)

        return self.repository.add(log)

    def create_log_from_import(self, data, source_file=None):
        """
        Tạo log từ một dòng dữ liệu đã được CNCImporter làm sạch.
        """
        normalized = self._normalize_data(data)

        normalized["source_file"] = (
            str(source_file).strip() if source_file else None
        )

        self._validate_log(normalized)

        log = CNCProductionLog(**normalized)

        return self.repository.add(log)

    # ==========================================================
    # Update
    # ==========================================================

    def update_log(self, log_id, data):
        log = self.repository.get_by_id(log_id)

        if log is None:
            raise NotFoundError(
                f"CNC Production Log not found: {log_id}"
            )

        normalized = self._normalize_data(data)

        self._validate_log(normalized)

        for field, value in normalized.items():
            setattr(log, field, value)

        self.repository.update()

        return log

    # ==========================================================
    # Delete
    # ==========================================================

    def delete_log(self, log_id):
        log = self.repository.get_by_id(log_id)

        if log is None:
            raise NotFoundError(
                f"CNC Production Log not found: {log_id}"
            )

        return self.repository.delete(log)

    # ==========================================================
    # Validation and normalization
    # ==========================================================

    @staticmethod
    def _validate_log(normalized):
        BaseValidator.required(
            normalized["machine_name"], "Machine Name"
        )
        BaseValidator.required(
            normalized["work_order_no"], "Work Order No"
        )

        if not normalized["machine_name"]:
            raise ValidationError("Machine Name is required.")

    @classmethod
    def _normalize_data(cls, data):
        data = dict(data or {})

        return {
            "log_date": cls._parse_date(data.get("log_date")),
            "machine_name": cls._clean_text(
                data.get("machine_name")
            ),
            "work_order_no": cls._clean_text(
                data.get("work_order_no")
            ).upper(),
            "product_name": cls._clean_optional_text(
                data.get("product_name")
            ),
            "operator_name": cls._clean_optional_text(
                data.get("operator_name")
            ),
            "operation": cls._clean_optional_text(
                data.get("operation")
            ),
            "shift": cls._clean_optional_text(
                data.get("shift")
            ),
            "actual_time_hours": cls._parse_float(
                data.get("actual_time_hours")
            ),
            "qty_ok": cls._parse_float(data.get("qty_ok")),
            "qty_ok_plus_ng": cls._parse_float(
                data.get("qty_ok_plus_ng")
            ),
            "total_ng": cls._parse_float(data.get("total_ng")),
            "raw_ng": cls._parse_float(data.get("raw_ng")),
            "process_ng": cls._parse_float(
                data.get("process_ng")
            ),
            "actual_pcs": cls._parse_float(
                data.get("actual_pcs")
            ),
            "standard_pcs": cls._parse_float(
                data.get("standard_pcs")
            ),
            "diff_pcs": cls._parse_float(
                data.get("diff_pcs")
            ),
            "source_file": cls._clean_optional_text(
                data.get("source_file")
            ),
        }

    @staticmethod
    def _clean_text(value):
        return str(value or "").strip()

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
            import pandas as pd

            if pd.isna(value):
                return None
        except Exception:
            pass

        try:
            return datetime.strptime(
                str(value)[:10], "%Y-%m-%d"
            ).date()
        except ValueError:
            return None
