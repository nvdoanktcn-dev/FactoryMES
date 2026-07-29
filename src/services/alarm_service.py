from __future__ import annotations

from datetime import datetime

from src.framework.exception import NotFoundError, ValidationError
from src.models.alarm import Alarm
from src.repository.alarm_repository import AlarmRepository
from src.services.base_service import SessionOwnedService
from src.services.machine_service import MachineService


class AlarmService(SessionOwnedService):
    """
    Giai đoạn 7 (MES Real-time, 2026-07-28): quản lý Alarm gắn với
    máy. Trước phase này, "Alarm" trên Dashboard chỉ là UI dựng sẵn
    không có dữ liệu thật đứng sau (xem `src/models/alarm.py`).

    Giống Giai đoạn 4/6, service MỚI này cần dữ liệu vừa ghi hiển thị
    ngay lập tức từ session/page khác (Alarm page mở nhanh sau Live
    Dashboard/Dashboard cần thấy alarm vừa raise) - gọi `self.commit()`
    sau mỗi create/update.
    """

    SEVERITY_INFO = "INFO"
    SEVERITY_WARNING = "WARNING"
    SEVERITY_ERROR = "ERROR"
    SEVERITY_CRITICAL = "CRITICAL"

    VALID_SEVERITIES = {
        SEVERITY_INFO,
        SEVERITY_WARNING,
        SEVERITY_ERROR,
        SEVERITY_CRITICAL,
    }

    STATUS_OPEN = "OPEN"
    STATUS_ACKNOWLEDGED = "ACKNOWLEDGED"
    STATUS_RESOLVED = "RESOLVED"

    VALID_STATUSES = {
        STATUS_OPEN,
        STATUS_ACKNOWLEDGED,
        STATUS_RESOLVED,
    }

    def __init__(
        self,
        session=None,
        machine_service=None,
    ):
        super().__init__(session=session)

        self.repository = AlarmRepository(self.session)

        self.machine_service = (
            machine_service
            or MachineService(session=self.session)
        )

    # ==========================================================
    # Query
    # ==========================================================

    def get_all(self, limit=None):
        return self.repository.get_all_ordered(limit=limit)

    def get_by_id(self, alarm_id):
        return self.repository.get_by_id(alarm_id)

    def get_open_alarms(self, limit=None):
        return self.repository.get_open_alarms(limit=limit)

    def get_by_machine(self, machine_code):
        machine = self._require_machine(machine_code)
        return self.repository.get_by_machine_id(machine.id)

    # ==========================================================
    # Create
    # ==========================================================

    def create_alarm(self, data):
        machine = self._require_machine(
            data.get("machine_code")
        )

        alarm = Alarm(
            machine_id=machine.id,
            machine_code=machine.machine_code,
            alarm_code=self._require_text(
                data.get("alarm_code"),
                "Alarm Code",
            ),
            message=self._require_text(
                data.get("message"),
                "Message",
            ),
            severity=self._normalize_severity(
                data.get("severity")
            ),
            status=self.STATUS_OPEN,
            remark=self._clean_optional_text(
                data.get("remark")
            ),
        )

        self.repository.add(alarm)

        self.commit()

        return alarm

    # ==========================================================
    # Status transitions
    # ==========================================================

    def acknowledge_alarm(
        self,
        alarm_id,
        *,
        acknowledged_by=None,
    ):
        alarm = self._require_alarm(alarm_id)

        if alarm.status == self.STATUS_RESOLVED:
            raise ValidationError(
                "Cannot acknowledge an alarm that is "
                "already RESOLVED."
            )

        alarm.status = self.STATUS_ACKNOWLEDGED
        alarm.acknowledged_at = datetime.now()
        alarm.acknowledged_by = self._clean_optional_upper(
            acknowledged_by
        )

        self.repository.update()

        self.commit()

        return alarm

    def resolve_alarm(
        self,
        alarm_id,
        *,
        resolved_by=None,
        remark=None,
    ):
        alarm = self._require_alarm(alarm_id)

        alarm.status = self.STATUS_RESOLVED
        alarm.resolved_at = datetime.now()
        alarm.resolved_by = self._clean_optional_upper(
            resolved_by
        )

        if remark:
            alarm.remark = self._clean_optional_text(
                remark
            )

        self.repository.update()

        self.commit()

        return alarm

    # ==========================================================
    # Validation
    # ==========================================================

    def _require_alarm(self, alarm_id):
        alarm = self.get_by_id(alarm_id)

        if alarm is None:
            raise NotFoundError(
                f"Alarm not found: {alarm_id}"
            )

        return alarm

    def _require_machine(self, machine_code):
        code = str(machine_code or "").strip().upper()

        if not code:
            raise ValidationError(
                "Machine Code is required."
            )

        machine = self.machine_service.get_by_code(code)

        if machine is None:
            raise NotFoundError(
                f"Machine not found: {code}"
            )

        return machine

    @classmethod
    def _normalize_severity(cls, value):
        normalized = str(
            value or cls.SEVERITY_WARNING
        ).strip().upper()

        if normalized not in cls.VALID_SEVERITIES:
            raise ValidationError(
                f"Invalid Severity: {normalized}"
            )

        return normalized

    @staticmethod
    def _require_text(value, field_name):
        text = str(value or "").strip()

        if not text:
            raise ValidationError(
                f"{field_name} is required."
            )

        return text

    @staticmethod
    def _clean_optional_upper(value):
        text = str(value or "").strip().upper()
        return text or None

    @staticmethod
    def _clean_optional_text(value):
        text = str(value or "").strip()
        return text or None

    # ==========================================================
    # Cleanup
    # ==========================================================

    def close(self):
        if self.machine_service is not None:
            self.machine_service.close()

        super().close()
