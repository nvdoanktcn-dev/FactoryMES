from __future__ import annotations

from datetime import datetime

from src.framework.exception import NotFoundError, ValidationError
from src.repository.alarm_repository import AlarmRepository
from src.repository.machine_status_log_repository import (
    MachineStatusLogRepository,
)
from src.services.base_service import SessionOwnedService
from src.services.machine_service import MachineService


class MachineStatusSnapshot:
    """
    1 dòng "trạng thái hiện tại" của 1 máy - dùng cho Live Dashboard.
    Không phải SQLAlchemy model, chỉ là 1 DTO đã ghép sẵn.
    """

    __slots__ = (
        "machine_id",
        "machine_code",
        "machine_name",
        "machine_type",
        "status",
        "status_since",
        "open_alarm_count",
    )

    def __init__(
        self,
        *,
        machine_id,
        machine_code,
        machine_name,
        machine_type,
        status,
        status_since,
        open_alarm_count,
    ):
        self.machine_id = machine_id
        self.machine_code = machine_code
        self.machine_name = machine_name
        self.machine_type = machine_type
        self.status = status
        self.status_since = status_since
        self.open_alarm_count = open_alarm_count


class MachineStatusService(SessionOwnedService):
    """
    Giai đoạn 7 (MES Real-time, 2026-07-28): facade cho màn hình Live
    Dashboard - đổi trạng thái máy nhanh (kèm ghi log qua
    `MachineService`), và tổng hợp "trạng thái hiện tại + đã ở trạng
    thái đó bao lâu + số alarm đang mở" cho toàn bộ máy chỉ bằng vài
    query, không phải N+1 query cho từng máy.

    Giống Giai đoạn 4/6, service này cần dữ liệu vừa ghi hiển thị
    NGAY LẬP TỨC từ session/page khác (đổi trạng thái ở Live
    Dashboard phải thấy ngay ở Machine Master và ngược lại) - nên gọi
    `self.commit()` sau mỗi lần đổi trạng thái, không chỉ flush.
    """

    # Trạng thái có thể đổi nhanh từ Live Dashboard. KHÔNG bao gồm
    # INACTIVE - đó là vòng đời "xoá mềm" của Machine Master
    # (MachineService.delete_machine()), không phải một trạng thái
    # vận hành "sống" giống RUNNING/IDLE/STOPPED/MAINTENANCE/ALARM.
    VALID_LIVE_STATUSES = {
        "RUNNING",
        "IDLE",
        "STOPPED",
        "MAINTENANCE",
        "ALARM",
    }

    def __init__(
        self,
        session=None,
        machine_service=None,
    ):
        super().__init__(session=session)

        self.machine_service = (
            machine_service
            or MachineService(session=self.session)
        )

        self.status_log_repository = (
            MachineStatusLogRepository(self.session)
        )

        self.alarm_repository = AlarmRepository(
            self.session
        )

    # ==========================================================
    # Live snapshot
    # ==========================================================

    def get_status_snapshot(self):
        machines = self.machine_service.get_all_machines()

        latest_by_machine = (
            self.status_log_repository
            .get_latest_by_machine_map()
        )

        open_alarm_counts = (
            self.alarm_repository
            .count_open_by_machine_map()
        )

        snapshot = []

        for machine in machines:
            latest_log = latest_by_machine.get(machine.id)

            snapshot.append(
                MachineStatusSnapshot(
                    machine_id=machine.id,
                    machine_code=machine.machine_code,
                    machine_name=machine.machine_name,
                    machine_type=machine.machine_type,
                    status=machine.status,
                    status_since=(
                        latest_log.changed_at
                        if latest_log is not None
                        else None
                    ),
                    open_alarm_count=(
                        open_alarm_counts.get(
                            machine.id, 0
                        )
                    ),
                )
            )

        return snapshot

    # ==========================================================
    # Change status
    # ==========================================================

    def change_status(
        self,
        machine_code,
        new_status,
        *,
        changed_by=None,
        remark=None,
    ):
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

        normalized_status = self._normalize_live_status(
            new_status
        )

        data = {
            "machine_code": machine.machine_code,
            "machine_name": machine.machine_name,
            "machine_type": machine.machine_type,
            "line": machine.line,
            "location": machine.location,
            "brand": machine.brand,
            "model": machine.model,
            "serial_number": machine.serial_number,
            "status": normalized_status,
        }

        normalized_changed_by = (
            str(changed_by).strip().upper()
            if changed_by
            else None
        )

        updated = self.machine_service.update_machine(
            code,
            data,
            status_source="LIVE_DASHBOARD",
            status_changed_by=normalized_changed_by,
            status_remark=remark,
        )

        self.commit()

        return updated

    # ==========================================================
    # History
    # ==========================================================

    def get_status_history(
        self,
        machine_code,
        limit=None,
    ):
        code = str(machine_code or "").strip().upper()
        machine = self.machine_service.get_by_code(code)

        if machine is None:
            raise NotFoundError(
                f"Machine not found: {code}"
            )

        return (
            self.status_log_repository
            .get_by_machine_id(
                machine.id,
                limit=limit,
            )
        )

    # ==========================================================
    # Validation
    # ==========================================================

    @classmethod
    def _normalize_live_status(cls, value):
        normalized = str(value or "").strip().upper()

        if normalized not in cls.VALID_LIVE_STATUSES:
            raise ValidationError(
                f"Invalid live status: {normalized}. "
                "Valid values: "
                f"{sorted(cls.VALID_LIVE_STATUSES)}"
            )

        return normalized

    # ==========================================================
    # Cleanup
    # ==========================================================

    def close(self):
        if self.machine_service is not None:
            self.machine_service.close()

        super().close()
