from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.repository.production_assignment_repository import (
    ProductionAssignmentRepository,
)


@dataclass(slots=True)
class ResourceConflict:
    assignment_id: int
    resource_type: str
    resource_code: str
    planned_start: datetime | None
    planned_finish: datetime | None

    def message(self) -> str:
        start_text = self._format_datetime(
            self.planned_start
        )
        finish_text = self._format_datetime(
            self.planned_finish
        )

        return (
            f"{self.resource_type} "
            f"{self.resource_code} conflicts with "
            f"Assignment #{self.assignment_id} "
            f"from {start_text} to {finish_text}"
        )

    @staticmethod
    def _format_datetime(
        value,
    ) -> str:
        if value is None:
            return "-"

        return value.strftime(
            "%Y-%m-%d %H:%M"
        )


class ResourceConflictService:
    """
    Kiểm tra xung đột tài nguyên khi Release Assignment.

    Nhân viên không bị ràng buộc cố định:
    - CNC hoặc ROBOT
    - ca ngày hoặc ca đêm

    Chỉ kiểm tra việc một tài nguyên không thể được
    phân công cho hai Assignment trùng thời gian.
    """

    BLOCKING_STATUSES = {
        "RELEASED",
        "IN_PROGRESS",
        "ON_HOLD",
    }

    def __init__(
        self,
        session,
    ):
        if session is None:
            raise ValueError(
                "SQLAlchemy session is required."
            )

        self.session = session

        self.repository = (
            ProductionAssignmentRepository(
                session
            )
        )

    def check_assignment_conflicts(
        self,
        assignment,
    ) -> list[ResourceConflict]:
        if assignment is None:
            raise ValueError(
                "Production Assignment is required."
            )

        if assignment.planned_start is None:
            raise ValueError(
                "Planned Start is required before release."
            )

        if assignment.planned_finish is None:
            raise ValueError(
                "Planned Finish is required before release."
            )

        if (
            assignment.planned_finish
            <= assignment.planned_start
        ):
            raise ValueError(
                (
                    "Planned Finish must be "
                    "after Planned Start."
                )
            )

        conflicts = []

        conflicts.extend(
            self.check_machine_conflicts(
                assignment
            )
        )

        conflicts.extend(
            self.check_employee_conflicts(
                assignment
            )
        )

        return conflicts

    def check_machine_conflicts(
        self,
        assignment,
    ) -> list[ResourceConflict]:
        machine_code = self._normalize_code(
            assignment.machine_code
        )

        if not machine_code:
            return []

        records = (
            self.repository
            .find_time_conflicts(
                machine_code=machine_code,
                employee_code=None,
                planned_start=(
                    assignment.planned_start
                ),
                planned_finish=(
                    assignment.planned_finish
                ),
                exclude_assignment_id=(
                    assignment.id
                ),
            )
        )

        return [
            ResourceConflict(
                assignment_id=record.id,
                resource_type="Machine",
                resource_code=machine_code,
                planned_start=record.planned_start,
                planned_finish=record.planned_finish,
            )
            for record in records
            if (
                self._normalize_code(
                    record.machine_code
                )
                == machine_code
                and self._normalize_status(
                    record.status
                )
                in self.BLOCKING_STATUSES
            )
        ]

    def check_employee_conflicts(
        self,
        assignment,
    ) -> list[ResourceConflict]:
        employee_code = self._normalize_code(
            assignment.employee_code
        )

        if not employee_code:
            return []

        records = (
            self.repository
            .find_time_conflicts(
                machine_code=None,
                employee_code=employee_code,
                planned_start=(
                    assignment.planned_start
                ),
                planned_finish=(
                    assignment.planned_finish
                ),
                exclude_assignment_id=(
                    assignment.id
                ),
            )
        )

        return [
            ResourceConflict(
                assignment_id=record.id,
                resource_type="Employee",
                resource_code=employee_code,
                planned_start=record.planned_start,
                planned_finish=record.planned_finish,
            )
            for record in records
            if (
                self._normalize_code(
                    record.employee_code
                )
                == employee_code
                and self._normalize_status(
                    record.status
                )
                in self.BLOCKING_STATUSES
            )
        ]

    def validate_release(
        self,
        assignment,
    ):
        conflicts = (
            self.check_assignment_conflicts(
                assignment
            )
        )

        if not conflicts:
            return True

        messages = [
            conflict.message()
            for conflict in conflicts
        ]

        raise ValueError(
            (
                "Resource conflict detected:\n\n"
                + "\n".join(messages)
            )
        )

    @staticmethod
    def _normalize_status(
        value,
    ) -> str:
        return str(
            value or ""
        ).strip().upper()

    @staticmethod
    def _normalize_code(
        value,
    ) -> str:
        return str(
            value or ""
        ).strip().upper()