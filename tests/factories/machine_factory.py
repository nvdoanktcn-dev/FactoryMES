from __future__ import annotations

from uuid import uuid4

from src.services.machine_service import (
    MachineService,
)


class MachineFactory:
    """
    Factory tạo Machine phục vụ integration test.
    """

    @staticmethod
    def build(**overrides):
        machine_type = str(
            overrides.get(
                "machine_type",
                "CNC",
            )
            or "CNC"
        ).strip().upper()

        if machine_type == "CNC":
            default_machine_code = (
                f"BLTEST{uuid4().hex[:8]}"
            ).upper()
        elif machine_type == "ROBOT":
            default_machine_code = (
                f"BRASK{uuid4().hex[:8]}"
            ).upper()
        else:
            default_machine_code = (
                f"TEST-{uuid4().hex[:8]}"
            ).upper()

        data = {
            "machine_code": default_machine_code,
            "machine_name": "Test Machine",
            "machine_type": machine_type,
            "line": "CNC",
            "location": "Factory 1",
            "brand": "Brother",
            "model": "S700",
            "serial_number": uuid4().hex,
            "status": "RUNNING",
        }

        data.update(overrides)

        return data

    @classmethod
    def create(
        cls,
        session,
        **overrides,
    ):
        service = MachineService(
            session=session
        )

        machine = service.create_machine(
            cls.build(**overrides)
        )

        session.flush()

        return machine

    @classmethod
    def create_running(
        cls,
        session,
        **overrides,
    ):
        return cls.create(
            session,
            status="RUNNING",
            **overrides,
        )

    @classmethod
    def create_stopped(
        cls,
        session,
        **overrides,
    ):
        return cls.create(
            session,
            status="STOPPED",
            **overrides,
        )

    @classmethod
    def create_maintenance(
        cls,
        session,
        **overrides,
    ):
        return cls.create(
            session,
            status="MAINTENANCE",
            **overrides,
        )

    @classmethod
    def create_inactive(
        cls,
        session,
        **overrides,
    ):
        return cls.create(
            session,
            status="INACTIVE",
            **overrides,
        )
