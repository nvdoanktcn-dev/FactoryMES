from __future__ import annotations

from src.models.employee import Employee
from src.repository.base_repository import (
    BaseRepository,
)


class EmployeeRepository(
    BaseRepository
):
    def __init__(
        self,
        session,
    ):
        super().__init__(
            session=session,
            model=Employee,
        )

    def get_by_code(
        self,
        employee_code,
    ):
        code = str(
            employee_code or ""
        ).strip().upper()

        if not code:
            return None

        return (
            self.session
            .query(Employee)
            .filter(
                Employee.employee_code == code
            )
            .first()
        )

    def exists(
        self,
        employee_code,
    ) -> bool:
        return (
            self.get_by_code(
                employee_code
            )
            is not None
        )