from __future__ import annotations

from src.database.session import get_session
from src.framework.base_service import BaseService
from src.framework.exception import DuplicateError, NotFoundError
from src.framework.validator import BaseValidator
from src.models.machine import Machine
from src.models.machine_status_log import MachineStatusLog
from src.repository.machine_repository import MachineRepository
from src.repository.machine_status_log_repository import (
    MachineStatusLogRepository,
)
from sqlalchemy.orm import Session

from src.services.base_service import SessionOwnedService
import re


class MachineService(SessionOwnedService):
    def __init__(
        self,
        session: Session | None = None,
        repository: MachineRepository | None = None,
    ) -> None:
        if repository is not None:
            repository_session = getattr(
                repository,
                "session",
                None,
            )

            super().__init__(
                session=repository_session,
            )

            self._owns_session = False
            self.repository = repository
            self.status_log_repository = (
                MachineStatusLogRepository(self.session)
            )
            return

        super().__init__(
            session=session,
        )

        self.repository = MachineRepository(
            self.require_session()
        )

        # Giai đoạn 7 (MES Real-time, 2026-07-28): mỗi lần
        # `machine.status` thay đổi (tạo mới, sửa qua form CRUD, xoá
        # mềm, hoặc đổi nhanh từ Live Dashboard), một dòng
        # `MachineStatusLog` được ghi tự động - đây là cách duy nhất
        # trạng thái được ghi log, giống hệt cách
        # `ProductionAssignmentService` tự ghi
        # `ProductionAssignmentHistory` mỗi khi trạng thái Assignment
        # đổi. Nhờ vậy MỌI máy (không chỉ máy vừa được đổi trạng thái
        # qua Live Dashboard) đều có lịch sử đầy đủ kể từ lúc tạo.
        self.status_log_repository = (
            MachineStatusLogRepository(self.session)
        )

    def get_all_machines(self):
        return self.repository.get_all()

    def get_machine(self, machine_code):
        code = self._normalize_code(machine_code)
        if not code:
            return None
        return self.repository.get_by_code(code)

    def get_by_code(self, machine_code):
        return self.get_machine(machine_code)

    def search_machines(self, keyword):
        machines = self.get_all_machines()
        text = str(keyword or "").strip().lower()
        if not text:
            return machines
        return [
            machine
            for machine in machines
            if text in str(machine.machine_code or "").lower()
            or text in str(machine.machine_name or "").lower()
            or text in str(machine.machine_type or "").lower()
            or text in str(machine.line or "").lower()
            or text in str(machine.location or "").lower()
            or text in str(machine.brand or "").lower()
            or text in str(machine.model or "").lower()
            or text in str(machine.serial_number or "").lower()
            or text in str(machine.status or "").lower()
        ]

    def create_machine(self, data):
        normalized = self._normalize_data(data)

        machine_code = normalized["machine_code"]
        machine_name = normalized["machine_name"]
        machine_type = normalized["machine_type"]

        self._validate_machine(
            machine_code,
            machine_name,
            machine_type,
        )

        if self.repository.get_by_code(machine_code) is not None:
            raise DuplicateError(
                f"Machine already exists: {machine_code}"
            )

        machine = Machine(**normalized)
        self.log_info(f"Create Machine: {machine_code}")
        machine = self.repository.add(machine)

        self._log_status_change(
            machine,
            old_status=None,
            new_status=machine.status,
            source="MACHINE_CREATED",
        )

        return machine

    def update_machine(
        self,
        machine_code,
        data,
        *,
        status_source="MACHINE_CRUD",
        status_changed_by=None,
        status_remark=None,
    ):
        code = self._normalize_code(machine_code)
        machine = self.repository.get_by_code(code)

        if machine is None:
            raise NotFoundError(
                f"Machine not found: {code}"
            )

        old_status = machine.status

        normalized = self._normalize_data(
            {**dict(data or {}), "machine_code": code}
        )
        self._validate_machine(
            code,
            normalized["machine_name"],
            normalized["machine_type"],
        )

        machine.machine_name = normalized["machine_name"]
        machine.machine_type = normalized["machine_type"]
        machine.line = normalized["line"]
        machine.location = normalized["location"]
        machine.brand = normalized["brand"]
        machine.model = normalized["model"]
        machine.serial_number = normalized["serial_number"]
        machine.status = normalized["status"]

        self.log_info(f"Update Machine: {code}")
        self.repository.update()

        self._log_status_change(
            machine,
            old_status=old_status,
            new_status=machine.status,
            source=status_source,
            changed_by=status_changed_by,
            remark=status_remark,
        )

        return machine

    def save_machine(self, data):
        if not isinstance(data, dict):
            raise ValueError(
                "Machine data must be a dictionary."
            )

        machine_code = self._normalize_code(
            data.get("machine_code")
        )

        if self.repository.get_by_code(machine_code) is None:
            return self.create_machine(data), "created"

        return (
            self.update_machine(machine_code, data),
            "updated",
        )

    def delete_machine(self, machine_code):
        code = self._normalize_code(machine_code)
        machine = self.repository.get_by_code(code)

        if machine is None:
            raise NotFoundError(
                f"Machine not found: {code}"
            )

        old_status = machine.status
        machine.status = "INACTIVE"
        self.log_warning(f"Inactive Machine: {code}")
        self.repository.update()

        self._log_status_change(
            machine,
            old_status=old_status,
            new_status="INACTIVE",
            source="MACHINE_DELETE",
        )

        return machine

    def _log_status_change(
        self,
        machine,
        *,
        old_status,
        new_status,
        source="MACHINE_CRUD",
        changed_by=None,
        remark=None,
    ):
        """
        Ghi 1 dòng MachineStatusLog nếu trạng thái thực sự thay đổi.
        Không làm gì (và không lỗi) nếu status_log_repository chưa
        được khởi tạo, để không phá vỡ bất kỳ chỗ nào khác đang tự
        tạo instance MachineService theo cách khác trong tương lai.
        """
        if old_status == new_status:
            return

        repository = getattr(
            self,
            "status_log_repository",
            None,
        )

        if repository is None:
            return

        repository.add(
            MachineStatusLog(
                machine_id=machine.id,
                machine_code=machine.machine_code,
                old_status=old_status,
                new_status=new_status,
                source=source,
                changed_by=changed_by,
                remark=remark,
            )
        )

    @staticmethod
    def _validate_machine(
        machine_code,
        machine_name,
        machine_type,
    ):
        BaseValidator.required(
            machine_code,
            "Machine Code",
        )

        BaseValidator.required(
            machine_name,
            "Machine Name",
        )

        BaseValidator.required(
            machine_type,
            "Machine Type",
        )

        BaseValidator.max_length(
            machine_code,
            "Machine Code",
            30,
        )

        BaseValidator.max_length(
            machine_name,
            "Machine Name",
            100,
        )

        normalized_code = str(
            machine_code
        ).strip().upper()

        normalized_type = str(
            machine_type
        ).strip().upper()

        if normalized_type == "CNC":
            if not re.fullmatch(
                r"BL[A-Z0-9]+",
                normalized_code,
            ):
                raise ValueError(
                    "Invalid CNC Machine Code."
                )

            return

        if normalized_type == "ROBOT":
            valid_br = re.fullmatch(
                r"BR(0[1-9]|1[01])",
                normalized_code,
            )

            valid_ask = re.fullmatch(
                r"ASK[A-Z0-9]+",
                normalized_code,
            )

            valid_brask = re.fullmatch(
                r"BRASK[A-Z0-9]+",
                normalized_code,
            )

            if not (
                valid_br
                or valid_ask
                or valid_brask
            ):
                raise ValueError(
                    "Invalid ROBOT Machine Code."
                )

            return

        raise ValueError(
            "Invalid Machine Type."
        )

    @classmethod
    def _normalize_data(cls, data):
        data = dict(data or {})
        return {
            "machine_code": cls._normalize_code(
                data.get("machine_code")
            ),
            "machine_name": cls._clean_text(
                data.get("machine_name")
            ),
            "machine_type": cls._clean_optional_text(
                data.get("machine_type")
            ),
            "line": cls._clean_optional_text(
                data.get("line")
            ),
            "location": cls._clean_optional_text(
                data.get("location")
            ),
            "brand": cls._clean_optional_text(
                data.get("brand")
            ),
            "model": cls._clean_optional_text(
                data.get("model")
            ),
            "serial_number": cls._clean_optional_text(
                data.get("serial_number")
            ),
            "status": cls._normalize_status(
                data.get("status")
            ),
        }

    @staticmethod
    def _normalize_code(value):
        return str(value or "").strip().upper()

    @staticmethod
    def _clean_text(value):
        return str(value or "").strip()

    @staticmethod
    def _clean_optional_text(value):
        text = str(value or "").strip()
        return text or None

    @staticmethod
    def _normalize_status(value):
        status = str(
            value or "RUNNING"
        ).strip().upper()

        mapping = {
            "ACTIVE": "RUNNING",
            "RUNNING": "RUNNING",

            "TOPPED": "STOPPED",

            "MAINTENANCE": "MAINTENANCE",
            "MAINSTOP": "STOPPED",
            "STAIN": "MAINTENANCE",
            "PM": "MAINTENANCE",

            "INACTIVE": "INACTIVE",

            "IDLE": "IDLE",
            "ALARM": "ALARM",
        }

        # Giai đoạn 7 (MES Real-time, 2026-07-28): "IDLE" trước đây bị
        # gộp nhầm vào "INACTIVE" (máy đã ngừng sử dụng/xoá mềm qua
        # delete_machine()) trong bảng ánh xạ trên - không gây lỗi
        # thực tế vì form Machine CRUD chưa từng có lựa chọn "IDLE",
        # nhưng sẽ sai hoàn toàn một khi IDLE trở thành trạng thái
        # thật (máy đang bật nhưng không chạy việc gì, khác hẳn máy đã
        # bị vô hiệu hoá). Đã tách "IDLE"/"ALARM" thành 2 giá trị hợp
        # lệ riêng biệt bên dưới.
        status = mapping.get(status, status)

        allowed = {
            "RUNNING",
            "IDLE",
            "STOPPED",
            "MAINTENANCE",
            "ALARM",
            "INACTIVE",
        }

        if status not in allowed:
            raise ValueError(
                f"Invalid Machine Status: {status}"
            )

        return status