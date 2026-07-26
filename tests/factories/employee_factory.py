from __future__ import annotations

from uuid import uuid4

from src.services.employee_service import (
    EmployeeService,
)


class EmployeeFactory:
    """
    Factory tạo Employee phục vụ integration test.
    """

    @staticmethod
    def build(**overrides):
        data = {
            "employee_code": (
                f"EMP-{uuid4().hex[:8]}"
            ).upper(),
            "employee_name": "Test Employee",
            "department": "PRODUCTION",
            "position": "OPERATOR",
            "shift": "DAY",
            "status": "ACTIVE",
            "remark": "Factory employee",
        }

        data.update(overrides)

        return data

    @classmethod
    def create(
        cls,
        session,
        **overrides,
    ):
        service = EmployeeService(
            session=session
        )

        employee = service.create_employee(
            cls.build(**overrides)
        )

        session.flush()

        return employee

    @classmethod
    def create_active(
        cls,
        session,
        **overrides,
    ):
        return cls.create(
            session,
            status="ACTIVE",
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