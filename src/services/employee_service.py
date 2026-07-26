from __future__ import annotations

from src.framework.exception import (
    DuplicateError,
    NotFoundError,
)
from src.framework.validator import BaseValidator
from src.models.employee import Employee
from src.repository.employee_repository import (
    EmployeeRepository,
)
from sqlalchemy.orm import Session

from src.services.base_service import SessionOwnedService


class EmployeeService(SessionOwnedService):
    STATUS_ACTIVE = "ACTIVE"
    STATUS_INACTIVE = "INACTIVE"

    VALID_STATUS = {
        STATUS_ACTIVE,
        STATUS_INACTIVE,
    }

    def __init__(
        self,
        session: Session | None = None,
        repository: EmployeeRepository | None = None,
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

        self.repository = EmployeeRepository(
            self.require_session()
        )
    # ==========================================================
    # Query
    # ==========================================================

    def get_all_employees(self):
        return self.repository.get_all()

    def get_employee(
        self,
        employee_code,
    ):
        code = self._normalize_code(
            employee_code
        )

        if not code:
            return None

        return self.repository.get_by_code(
            code
        )

    def get_by_code(
        self,
        employee_code,
    ):
        return self.get_employee(
            employee_code
        )

    def search_employees(
        self,
        keyword,
    ):
        employees = self.get_all_employees()

        text = str(
            keyword or ""
        ).strip().lower()

        if not text:
            return employees

        return [
            employee
            for employee in employees
            if (
                text
                in str(
                    employee.employee_code or ""
                ).lower()
                or text
                in str(
                    employee.employee_name or ""
                ).lower()
                or text
                in str(
                    employee.department or ""
                ).lower()
                or text
                in str(
                    employee.position or ""
                ).lower()
                or text
                in str(
                    employee.shift or ""
                ).lower()
                or text
                in str(
                    employee.status or ""
                ).lower()
            )
        ]

    # ==========================================================
    # Create
    # ==========================================================

    def create_employee(
        self,
        data,
    ):
        normalized = self._normalize_data(
            data
        )

        employee_code = normalized[
            "employee_code"
        ]

        employee_name = normalized[
            "employee_name"
        ]

        self._validate_employee(
            employee_code=employee_code,
            employee_name=employee_name,
        )

        if self.repository.exists(
            employee_code
        ):
            raise DuplicateError(
                (
                    "Employee already exists: "
                    f"{employee_code}"
                )
            )

        employee = Employee(
            **normalized
        )

        self.log_info(
            f"Create Employee: {employee_code}"
        )

        return self.repository.add(
            employee
        )

    # ==========================================================
    # Update
    # ==========================================================

    def update_employee(
        self,
        employee_code,
        data,
    ):
        code = self._normalize_code(
            employee_code
        )

        employee = self.repository.get_by_code(
            code
        )

        if employee is None:
            raise NotFoundError(
                f"Employee not found: {code}"
            )

        normalized = self._normalize_data(
            {
                **dict(data or {}),
                "employee_code": code,
            }
        )

        self._validate_employee(
            employee_code=code,
            employee_name=normalized[
                "employee_name"
            ],
        )

        employee.employee_name = normalized[
            "employee_name"
        ]

        employee.department = normalized[
            "department"
        ]

        employee.position = normalized[
            "position"
        ]

        employee.shift = normalized[
            "shift"
        ]

        employee.status = normalized[
            "status"
        ]

        employee.remark = normalized[
            "remark"
        ]

        self.log_info(
            f"Update Employee: {code}"
        )

        self.repository.update()

        return employee

    # ==========================================================
    # Upsert for Import
    # ==========================================================

    def save_employee(
        self,
        data,
    ):
        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "Employee data must be a dictionary."
            )

        employee_code = self._normalize_code(
            data.get(
                "employee_code"
            )
        )

        existing = self.repository.get_by_code(
            employee_code
        )

        if existing is None:
            employee = self.create_employee(
                data
            )

            return employee, "created"

        employee = self.update_employee(
            employee_code,
            data,
        )

        return employee, "updated"

    # ==========================================================
    # Inactive
    # ==========================================================

    def delete_employee(
        self,
        employee_code,
    ):
        return self.set_employee_status(
            employee_code,
            self.STATUS_INACTIVE,
        )

    def activate_employee(
        self,
        employee_code,
    ):
        return self.set_employee_status(
            employee_code,
            self.STATUS_ACTIVE,
        )

    def set_employee_status(
        self,
        employee_code,
        status,
    ):
        code = self._normalize_code(
            employee_code
        )

        employee = self.repository.get_by_code(
            code
        )

        if employee is None:
            raise NotFoundError(
                f"Employee not found: {code}"
            )

        normalized_status = self._normalize_status(
            status
        )
        employee.status = normalized_status

        self.log_info(
            (
                f"Set Employee Status: "
                f"{code} -> {normalized_status}"
            )
        )

        self.repository.update()

        return employee

    # ==========================================================
    # Transaction
    # ==========================================================

    def commit_changes(self) -> None:
        self.require_session().commit()

    def rollback_changes(self) -> None:
        session = self.require_session()

        if session.is_active:
            session.rollback()

    # ==========================================================
    # Validation and normalization
    # ==========================================================

    @staticmethod
    def _validate_employee(
        employee_code,
        employee_name,
    ):
        BaseValidator.required(
            employee_code,
            "Employee Code",
        )

        BaseValidator.required(
            employee_name,
            "Employee Name",
        )

        BaseValidator.max_length(
            employee_code,
            "Employee Code",
            30,
        )

        BaseValidator.max_length(
            employee_name,
            "Employee Name",
            100,
        )

    @classmethod
    def _normalize_data(
        cls,
        data,
    ):
        data = dict(
            data or {}
        )

        return {
            "employee_code": (
                cls._normalize_code(
                    data.get(
                        "employee_code"
                    )
                )
            ),
            "employee_name": (
                cls._clean_text(
                    data.get(
                        "employee_name"
                    )
                )
            ),
            "department": (
                cls._clean_optional_text(
                    data.get(
                        "department"
                    )
                )
            ),
            "position": (
                cls._clean_optional_text(
                    data.get(
                        "position"
                    )
                )
            ),
            "shift": (
                cls._normalize_shift(
                    data.get(
                        "shift"
                    )
                )
            ),
            "status": (
                cls._normalize_status(
                    data.get(
                        "status"
                    )
                )
            ),
            "remark": (
                cls._clean_optional_text(
                    data.get(
                        "remark"
                    )
                )
            ),
        }

    @staticmethod
    def _normalize_code(
        value,
    ):
        return str(
            value or ""
        ).strip().upper()

    @staticmethod
    def _clean_text(
        value,
    ):
        return str(
            value or ""
        ).strip()

    @staticmethod
    def _clean_optional_text(
        value,
    ):
        text = str(
            value or ""
        ).strip()

        return text or None

    @staticmethod
    def _normalize_shift(
        value,
    ):
        shift = str(
            value or ""
        ).strip().upper()

        if not shift:
            return None

        mapping = {
            "DAY": "DAY",
            "D": "DAY",
            "NGÀY": "DAY",
            "CA NGÀY": "DAY",
            "NIGHT": "NIGHT",
            "N": "NIGHT",
            "ĐÊM": "NIGHT",
            "CA ĐÊM": "NIGHT",
        }

        normalized = mapping.get(
            shift
        )

        if normalized is None:
            raise ValueError(
                f"Invalid Employee Shift: {shift}"
            )

        return normalized

    @classmethod
    def _normalize_status(
        cls,
        value,
    ):
        status = str(
            value
            or cls.STATUS_ACTIVE
        ).strip().upper()

        if status not in cls.VALID_STATUS:
            raise ValueError(
                (
                    "Invalid Employee Status: "
                    f"{status}"
                )
            )

        return status
