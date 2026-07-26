from __future__ import annotations

from sqlalchemy.orm import Session

from src.framework.exception import DuplicateError, NotFoundError
from src.framework.validator import BaseValidator
from src.models.cnc_machine import CNCMachine
from src.repository.cnc_machine_repository import CNCMachineRepository
from src.services.base_service import SessionOwnedService


class CNCMachineService(SessionOwnedService):
    """
    Service quản lý danh mục máy CNC.

    Theo cùng pattern với EmployeeService/MachineService: CRUD +
    search phía client, status dùng để deactivate thay vì xóa cứng.
    """

    STATUS_ACTIVE = "ACTIVE"
    STATUS_INACTIVE = "INACTIVE"

    VALID_STATUS = {
        STATUS_ACTIVE,
        STATUS_INACTIVE,
    }

    def __init__(
        self,
        session: Session | None = None,
        repository: CNCMachineRepository | None = None,
    ) -> None:
        if repository is not None:
            super().__init__(
                session=getattr(repository, "session", None)
            )
            self._owns_session = False
            self.repository = repository
            return

        super().__init__(session=session)

        self.repository = CNCMachineRepository(
            self.require_session()
        )

    # ==========================================================
    # Query
    # ==========================================================

    def get_all_cnc_machines(self):
        return self.repository.get_all()

    def get_cnc_machine(self, machine_code):
        code = self._normalize_code(machine_code)

        if not code:
            return None

        return self.repository.get_by_code(code)

    def get_by_code(self, machine_code):
        return self.get_cnc_machine(machine_code)

    def search_cnc_machines(self, keyword):
        machines = self.get_all_cnc_machines()

        text = str(keyword or "").strip().lower()

        if not text:
            return machines

        return [
            machine
            for machine in machines
            if (
                text in str(machine.machine_code or "").lower()
                or text in str(machine.machine_name or "").lower()
                or text in str(machine.machine_type or "").lower()
                or text in str(machine.controller or "").lower()
                or text in str(machine.location or "").lower()
                or text in str(machine.status or "").lower()
            )
        ]

    # ==========================================================
    # Create
    # ==========================================================

    def create_cnc_machine(self, data):
        normalized = self._normalize_data(data)

        machine_code = normalized["machine_code"]
        machine_name = normalized["machine_name"]

        self._validate_machine(
            machine_code=machine_code,
            machine_name=machine_name,
        )

        if self.repository.exists(machine_code):
            raise DuplicateError(
                f"CNC Machine already exists: {machine_code}"
            )

        machine = CNCMachine(**normalized)

        self.log_info(f"Create CNC Machine: {machine_code}")

        return self.repository.add(machine)

    # ==========================================================
    # Update
    # ==========================================================

    def update_cnc_machine(self, machine_code, data):
        code = self._normalize_code(machine_code)

        machine = self.repository.get_by_code(code)

        if machine is None:
            raise NotFoundError(f"CNC Machine not found: {code}")

        normalized = self._normalize_data(
            {**dict(data or {}), "machine_code": code}
        )

        self._validate_machine(
            machine_code=code,
            machine_name=normalized["machine_name"],
        )

        machine.machine_name = normalized["machine_name"]
        machine.machine_type = normalized["machine_type"]
        machine.controller = normalized["controller"]
        machine.axis_count = normalized["axis_count"]
        machine.location = normalized["location"]
        machine.status = normalized["status"]
        machine.remark = normalized["remark"]

        self.log_info(f"Update CNC Machine: {code}")

        self.repository.update()

        return machine

    # ==========================================================
    # Deactivate
    # ==========================================================

    def delete_cnc_machine(self, machine_code):
        code = self._normalize_code(machine_code)

        machine = self.repository.get_by_code(code)

        if machine is None:
            raise NotFoundError(f"CNC Machine not found: {code}")

        machine.status = self.STATUS_INACTIVE

        self.log_warning(f"Inactive CNC Machine: {code}")

        self.repository.update()

        return machine

    # ==========================================================
    # Validation and normalization
    # ==========================================================

    @staticmethod
    def _validate_machine(machine_code, machine_name):
        BaseValidator.required(machine_code, "Machine Code")
        BaseValidator.required(machine_name, "Machine Name")
        BaseValidator.max_length(machine_code, "Machine Code", 30)
        BaseValidator.max_length(machine_name, "Machine Name", 100)

    @classmethod
    def _normalize_data(cls, data):
        data = dict(data or {})

        axis_count = data.get("axis_count")

        try:
            axis_count = (
                int(axis_count)
                if axis_count not in (None, "")
                else None
            )
        except (TypeError, ValueError):
            axis_count = None

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
            "controller": cls._clean_optional_text(
                data.get("controller")
            ),
            "axis_count": axis_count,
            "location": cls._clean_optional_text(
                data.get("location")
            ),
            "status": cls._normalize_status(
                data.get("status")
            ),
            "remark": cls._clean_optional_text(
                data.get("remark")
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

    @classmethod
    def _normalize_status(cls, value):
        status = str(value or cls.STATUS_ACTIVE).strip().upper()

        if status not in cls.VALID_STATUS:
            raise ValueError(f"Invalid CNC Machine Status: {status}")

        return status
