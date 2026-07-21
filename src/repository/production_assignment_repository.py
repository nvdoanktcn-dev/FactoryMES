from __future__ import annotations

from sqlalchemy import or_

from src.models.production_assignment import (
    ProductionAssignment,
)
from src.repository.base_repository import (
    BaseRepository,
)


class ProductionAssignmentRepository(
    BaseRepository
):
    def __init__(
        self,
        session,
    ):
        super().__init__(
            session=session,
            model=ProductionAssignment,
        )

    def get_by_id(
        self,
        assignment_id,
    ):
        try:
            normalized_id = int(
                assignment_id
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        return (
            self.session
            .query(ProductionAssignment)
            .filter(
                ProductionAssignment.id
                == normalized_id
            )
            .first()
        )

    def get_by_production_order_id(
        self,
        production_order_id,
    ):
        try:
            normalized_id = int(
                production_order_id
            )
        except (
            TypeError,
            ValueError,
        ):
            return []

        return (
            self.session
            .query(ProductionAssignment)
            .filter(
                ProductionAssignment
                .production_order_id
                == normalized_id
            )
            .order_by(
                ProductionAssignment
                .planned_start
                .asc(),
                ProductionAssignment.id.asc(),
            )
            .all()
        )

    def get_by_machine(
        self,
        machine_code,
    ):
        code = str(
            machine_code or ""
        ).strip().upper()

        if not code:
            return []

        return (
            self.session
            .query(ProductionAssignment)
            .filter(
                ProductionAssignment.machine_code
                == code
            )
            .order_by(
                ProductionAssignment
                .planned_start
                .asc()
            )
            .all()
        )

    def get_by_employee(
        self,
        employee_code,
    ):
        code = str(
            employee_code or ""
        ).strip().upper()

        if not code:
            return []

        return (
            self.session
            .query(ProductionAssignment)
            .filter(
                ProductionAssignment.employee_code
                == code
            )
            .order_by(
                ProductionAssignment
                .planned_start
                .asc()
            )
            .all()
        )

    def get_active_assignments(self):
        return (
            self.session
            .query(ProductionAssignment)
            .filter(
                ProductionAssignment.status.in_(
                    [
                        "DRAFT",
                        "RELEASED",
                        "IN_PROGRESS",
                        "ON_HOLD",
                    ]
                )
            )
            .order_by(
                ProductionAssignment
                .planned_start
                .asc()
            )
            .all()
        )

    def find_time_conflicts(
        self,
        *,
        machine_code=None,
        employee_code=None,
        planned_start,
        planned_finish,
        exclude_assignment_id=None,
    ):
        query = (
            self.session
            .query(ProductionAssignment)
            .filter(
                ProductionAssignment.status.notin_(
                    [
                        "COMPLETED",
                        "CANCELLED",
                    ]
                ),
                ProductionAssignment.planned_start
                < planned_finish,
                ProductionAssignment.planned_finish
                > planned_start,
            )
        )

        resource_conditions = []

        normalized_machine = str(
            machine_code or ""
        ).strip().upper()

        normalized_employee = str(
            employee_code or ""
        ).strip().upper()

        if normalized_machine:
            resource_conditions.append(
                ProductionAssignment.machine_code
                == normalized_machine
            )

        if normalized_employee:
            resource_conditions.append(
                ProductionAssignment.employee_code
                == normalized_employee
            )

        if not resource_conditions:
            return []

        query = query.filter(
            or_(
                *resource_conditions
            )
        )

        if exclude_assignment_id is not None:
            query = query.filter(
                ProductionAssignment.id
                != int(exclude_assignment_id)
            )

        return query.all()