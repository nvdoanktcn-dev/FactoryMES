from __future__ import annotations

import re

from src.framework.exception import DuplicateError, NotFoundError
from src.framework.validator import BaseValidator
from src.models.machine import Machine
from src.repository.machine_repository import MachineRepository
from sqlalchemy.orm import Session

from src.services.base_service import SessionOwnedService


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
            return

        super().__init__(
            session=session,
        )

        self.repository = MachineRepository(
            self.require_session()
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
        self._validate_machine(
            machine_code,
            machine_name,
            normalized["machine_type"],
        )

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
        return self.set_machine_status(
            machine_code,
            "INACTIVE",
        )

    def activate_machine(self, machine_code):
        return self.set_machine_status(
            machine_code,
            "RUNNING",
        )

    def set_machine_status(
        self,
        machine_code,
        status,
    ):
        code = self._normalize_code(machine_code)
        machine = self.repository.get_by_code(code)

        if machine is None:
            raise NotFoundError(
                f"Machine not found: {code}"
            )

        normalized_status = self._normalize_status(
            status
        )
        machine.status = normalized_status

        self.log_info(
            (
                f"Set Machine Status: "
                f"{code} -> {normalized_status}"
            )
        )
        self.repository.update()
        return machine

    def commit_changes(self) -> None:
        self.require_session().commit()

    def rollback_changes(self) -> None:
        session = self.require_session()

        if session.is_active:
            session.rollback()

    @staticmethod
    def _validate_machine(
        machine_code,
        machine_name,
        machine_type=None,
    ):
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

        normalized_type = str(
            machine_type or ""
        ).strip().upper()

        if normalized_type == "CNC":
            if not machine_code.startswith("BL"):
                raise ValueError(
                    "CNC Machine Code must start with BL."
                )

        elif normalized_type == "ROBOT":
            if not MachineService._is_robot_code(
                machine_code
            ):
                raise ValueError(
                    (
                        "ROBOT Machine Code must be "
                        "BR01-BR11, ASK followed by digits, "
                        "or start with BRASK."
                    )
                )

        if machine_code.startswith("BL"):
            if normalized_type != "CNC":
                raise ValueError(
                    "BL Machine Code requires Machine Type CNC."
                )

        elif MachineService._looks_like_robot_code(
            machine_code
        ):
            if normalized_type != "ROBOT":
                raise ValueError(
                    (
                        "BR/ASK/BRASK Machine Code requires "
                        "Machine Type ROBOT."
                    )
                )

            if not MachineService._is_robot_code(
                machine_code
            ):
                raise ValueError(
                    (
                        "Robot code must be BR01-BR11 "
                        "ASK followed by digits, "
                        "or start with BRASK."
                    )
                )

    @staticmethod
    def _looks_like_robot_code(machine_code):
        return (
            machine_code.startswith("BR")
            or machine_code.startswith("ASK")
        )

    @staticmethod
    def _is_robot_code(machine_code):
        if (
            re.fullmatch(
                r"BRASK[A-Z0-9-]+",
                machine_code,
            )
            is not None
        ):
            return True

        br_match = re.fullmatch(
            r"BR(\d{2})",
            machine_code,
        )

        if br_match is not None:
            number = int(br_match.group(1))
            return 1 <= number <= 11

        return (
            re.fullmatch(
                r"ASK\d+",
                machine_code,
            )
            is not None
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
            "machine_type": cls._normalize_machine_type(
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
    def _normalize_machine_type(value):
        machine_type = str(
            value or ""
        ).strip().upper()

        if not machine_type:
            return None

        allowed = {
            "CNC",
            "ROBOT",
            "MANUAL",
            "INSPECTION",
            "OTHER",
        }

        if machine_type not in allowed:
            raise ValueError(
                f"Invalid Machine Type: {machine_type}"
            )

        return machine_type

    @staticmethod
    def _normalize_status(value):
        status = str(
            value or "RUNNING"
        ).strip().upper()

        mapping = {
            "ACTIVE": "RUNNING",
            "READY": "RUNNING",
            "RUNNING": "RUNNING",

            "TOPPED": "STOPPED",
            "STOPPED": "STOPPED",

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
