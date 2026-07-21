from __future__ import annotations

from src.database.session import get_session
from src.framework.base_service import BaseService
from src.framework.exception import DuplicateError, NotFoundError
from src.framework.validator import BaseValidator
from src.models.machine import Machine
from src.repository.machine_repository import MachineRepository


class MachineService(BaseService):
    def __init__(self, session=None):
        super().__init__()
        self._owns_session = session is None
        self.session = session or get_session()
        self.repository = MachineRepository(self.session)

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
        self._validate_machine(machine_code, machine_name)

        if self.repository.get_by_code(machine_code) is not None:
            raise DuplicateError(
                f"Machine already exists: {machine_code}"
            )

        machine = Machine(**normalized)
        self.log_info(f"Create Machine: {machine_code}")
        return self.repository.add(machine)

    def update_machine(self, machine_code, data):
        code = self._normalize_code(machine_code)
        machine = self.repository.get_by_code(code)

        if machine is None:
            raise NotFoundError(
                f"Machine not found: {code}"
            )

        normalized = self._normalize_data(
            {**dict(data or {}), "machine_code": code}
        )
        self._validate_machine(
            code,
            normalized["machine_name"],
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

        machine.status = "INACTIVE"
        self.log_warning(f"Inactive Machine: {code}")
        self.repository.update()
        return machine

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        if self._owns_session:
            self.session.close()

    @staticmethod
    def _validate_machine(machine_code, machine_name):
        BaseValidator.required(machine_code, "Machine Code")
        BaseValidator.required(machine_name, "Machine Name")
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
            "IDLE": "INACTIVE",
        }

        status = mapping.get(status, status)

        allowed = {
            "RUNNING",
            "STOPPED",
            "MAINTENANCE",
            "INACTIVE",
        }

        if status not in allowed:
            raise ValueError(
                f"Invalid Machine Status: {status}"
            )

        return status