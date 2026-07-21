from __future__ import annotations

from datetime import date, datetime

from src.database.session import get_session
from src.framework.base_service import BaseService
from src.framework.exception import (
    NotFoundError,
)
from src.models.production_assignment import (
    ProductionAssignment,
)
from src.models.production_order import (
    ProductionOrder,
)
from src.repository.production_assignment_repository import (
    ProductionAssignmentRepository,
)
from src.services.employee_service import (
    EmployeeService,
)
from src.services.machine_service import (
    MachineService,
)
from src.services.production_assignment_history_service import (
    ProductionAssignmentHistoryService,
)
from src.services.resource_conflict_service import (
    ResourceConflictService,
)


class ProductionAssignmentService(
    BaseService
):
    STATUS_DRAFT = "DRAFT"
    STATUS_RELEASED = "RELEASED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_ON_HOLD = "ON_HOLD"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"

    VALID_STATUSES = {
        STATUS_DRAFT,
        STATUS_RELEASED,
        STATUS_IN_PROGRESS,
        STATUS_ON_HOLD,
        STATUS_COMPLETED,
        STATUS_CANCELLED,
    }

    def __init__(
        self,
        session=None,
    ):
        super().__init__()

        self._owns_session = (
            session is None
        )

        self.session = session if session is not None else get_session()

        self.repository = ProductionAssignmentRepository(self.session)

        self.machine_service = MachineService(
            session=self.session
        )

        self.employee_service = EmployeeService(
            session=self.session
        )

        self.history_service = ProductionAssignmentHistoryService(self.session)

        self.conflict_service = ResourceConflictService(self.session)

    # ==========================================================
    # Query
    # ==========================================================

    def get_all_assignments(self):
        return self.repository.get_all()

    def get_assignment(
        self,
        assignment_id,
    ):
        return self.repository.get_by_id(
            assignment_id
        )

    def get_by_production_order_id(
        self,
        production_order_id,
    ):
        return (
            self.repository
            .get_by_production_order_id(
                production_order_id
            )
        )

    def get_by_machine(
        self,
        machine_code,
    ):
        return self.repository.get_by_machine(
            machine_code
        )

    def get_by_employee(
        self,
        employee_code,
    ):
        return self.repository.get_by_employee(
            employee_code
        )

    def get_active_assignments(self):
        return (
            self.repository
            .get_active_assignments()
        )

    # ==========================================================
    # Create
    # ==========================================================

    def create_assignment(
        self,
        data,
    ):
        normalized = self._normalize_data(
            data
        )

        production_order = (
            self._require_production_order(
                normalized[
                    "production_order_id"
                ]
            )
        )

        self._validate_resources(
            machine_code=normalized[
                "machine_code"
            ],
            employee_code=normalized[
                "employee_code"
            ],
        )

        self._validate_assignment(
            normalized,
            production_order,
        )

        assignment = ProductionAssignment(
            production_order_id=normalized[
                "production_order_id"
            ],
            machine_code=normalized[
                "machine_code"
            ],
            employee_code=normalized[
                "employee_code"
            ],
            shift=normalized[
                "shift"
            ],
            planned_start=normalized[
                "planned_start"
            ],
            planned_finish=normalized[
                "planned_finish"
            ],
            status=normalized[
                "status"
            ],
            assigned_at=(
                normalized["assigned_at"]
                or datetime.now()
            ),
            released_at=normalized[
                "released_at"
            ],
            actual_start=normalized[
                "actual_start"
            ],
            actual_finish=normalized[
                "actual_finish"
            ],
            remark=normalized[
                "remark"
            ],
        )

        self.log_info(
            (
                "Create Production Assignment: "
                f"ProductionOrder ID "
                f"{production_order.id}"
            )
        )

        assignment = self.repository.add(
            assignment
        )

        self.session.flush()

        self.history_service.record(
            assignment=assignment,
            action="CREATE",
            old_data={},
            new_data=self._snapshot(
                assignment
            ),
        )

        return assignment

    # ==========================================================
    # Update
    # ==========================================================

    def update_assignment(
        self,
        assignment_id,
        data,
    ):
        assignment = self._require_assignment(
            assignment_id
        )

        old_data = self._snapshot(
            assignment
        )

        if assignment.status in {
            self.STATUS_IN_PROGRESS,
            self.STATUS_COMPLETED,
            self.STATUS_CANCELLED,
        }:
            raise ValueError(
                (
                    "Cannot edit assignment when "
                    f"status is {assignment.status}."
                )
            )

        normalized = self._normalize_data(
            {
                **dict(data or {}),
                "production_order_id": (
                    assignment.production_order_id
                ),
                "status": assignment.status,
                "assigned_at": (
                    assignment.assigned_at
                ),
                "released_at": (
                    assignment.released_at
                ),
                "actual_start": (
                    assignment.actual_start
                ),
                "actual_finish": (
                    assignment.actual_finish
                ),
            }
        )

        production_order = (
            self._require_production_order(
                assignment.production_order_id
            )
        )

        self._validate_resources(
            machine_code=normalized[
                "machine_code"
            ],
            employee_code=normalized[
                "employee_code"
            ],
        )

        self._validate_assignment(
            normalized,
            production_order,
        )

        assignment.machine_code = normalized[
            "machine_code"
        ]
        assignment.employee_code = normalized[
            "employee_code"
        ]
        assignment.shift = normalized[
            "shift"
        ]
        assignment.planned_start = normalized[
            "planned_start"
        ]
        assignment.planned_finish = normalized[
            "planned_finish"
        ]
        assignment.remark = normalized[
            "remark"
        ]

        self.repository.update()

        self._record_history(
            assignment=assignment,
            action="UPDATE",
            old_data=old_data,
        )

        return assignment

    # ==========================================================
    # Domain behaviour
    # ==========================================================

    def assign_machine(
        self,
        assignment_id,
        machine_code,
    ):
        assignment = self._require_editable(
            assignment_id
        )

        old_data = self._snapshot(
            assignment
        )

        code = self._normalize_code(
            machine_code
        )

        if code:
            self._require_active_machine(
                code
            )

        assignment.machine_code = (
            code or None
        )

        self.repository.update()

        self._record_history(
            assignment=assignment,
            action="ASSIGN_MACHINE",
            old_data=old_data,
        )

        return assignment

    def assign_employee(
        self,
        assignment_id,
        employee_code,
    ):
        assignment = self._require_editable(
            assignment_id
        )

        old_data = self._snapshot(
            assignment
        )

        code = self._normalize_code(
            employee_code
        )

        if code:
            self._require_active_employee(
                code
            )

        # Không kiểm tra CNC/ROBOT hoặc ca cố định.
        assignment.employee_code = (
            code or None
        )

        self.repository.update()

        self._record_history(
            assignment=assignment,
            action="ASSIGN_EMPLOYEE",
            old_data=old_data,
        )

        return assignment

    def assign_shift(
        self,
        assignment_id,
        shift,
    ):
        assignment = self._require_editable(
            assignment_id
        )

        old_data = self._snapshot(
            assignment
        )

        assignment.shift = (
            self._normalize_upper(
                shift
            )
            or None
        )

        self.repository.update()

        self._record_history(
            assignment=assignment,
            action="ASSIGN_SHIFT",
            old_data=old_data,
        )

        return assignment

    def release(
        self,
        assignment_id,
    ):
        assignment = self._require_assignment(
            assignment_id
        )

        old_data = self._snapshot(
            assignment
        )

        if assignment.status not in {
            self.STATUS_DRAFT,
            self.STATUS_ON_HOLD,
        }:
            raise ValueError(
                (
                    "Only DRAFT or ON_HOLD "
                    "assignments can be released."
                )
            )

        production_order = (
            self._require_production_order(
                assignment.production_order_id
            )
        )

        if not assignment.employee_code:
            raise ValueError(
                (
                    "Employee must be assigned "
                    "before release."
                )
            )

        if (
            production_order.machine_type
            and not assignment.machine_code
        ):
            raise ValueError(
                (
                    "Machine must be assigned "
                    "before release."
                )
            )

        if not assignment.shift:
            raise ValueError(
                (
                    "Shift must be assigned "
                    "before release."
                )
            )

        self.conflict_service.validate_release(
            assignment
        )

        old_data = self._snapshot(
            assignment
        )

        assignment.status = (
            self.STATUS_RELEASED
        )
        assignment.released_at = (
            datetime.now()
        )

        self.repository.update()

        self._record_history(
            assignment=assignment,
            action="RELEASE",
            old_data=old_data,
        )

        return assignment

    def start(
        self,
        assignment_id,
        actual_start=None,
    ):
        assignment = self._require_assignment(
            assignment_id
        )

        old_data = self._snapshot(
            assignment
        )

        if assignment.status != (
            self.STATUS_RELEASED
        ):
            raise ValueError(
                (
                    "Only RELEASED assignments "
                    "can be started."
                )
            )

        assignment.status = (
            self.STATUS_IN_PROGRESS
        )

        assignment.actual_start = (
            self._normalize_datetime(
                actual_start
            )
            or datetime.now()
        )

        self.repository.update()

        self._record_history(
            assignment=assignment,
            action="START",
            old_data=old_data,
        )

        return assignment

    def hold(
        self,
        assignment_id,
    ):
        assignment = self._require_assignment(
            assignment_id
        )

        old_data = self._snapshot(
            assignment
        )

        if assignment.status != (
            self.STATUS_IN_PROGRESS
        ):
            raise ValueError(
                (
                    "Only IN_PROGRESS assignments "
                    "can be put on hold."
                )
            )

        assignment.status = (
            self.STATUS_ON_HOLD
        )

        self.repository.update()

        self._record_history(
            assignment=assignment,
            action="HOLD",
            old_data=old_data,
        )

        return assignment

    def complete(
        self,
        assignment_id,
        actual_finish=None,
    ):
        assignment = self._require_assignment(
            assignment_id
        )

        old_data = self._snapshot(
            assignment
        )

        if assignment.status not in {
            self.STATUS_IN_PROGRESS,
            self.STATUS_ON_HOLD,
        }:
            raise ValueError(
                (
                    "Only IN_PROGRESS or ON_HOLD "
                    "assignments can be completed."
                )
            )

        assignment.status = (
            self.STATUS_COMPLETED
        )

        assignment.actual_finish = (
            self._normalize_datetime(
                actual_finish
            )
            or datetime.now()
        )

        self.repository.update()

        self._record_history(
            assignment=assignment,
            action="COMPLETE",
            old_data=old_data,
        )

        return assignment

    def cancel(
        self,
        assignment_id,
    ):
        assignment = self._require_assignment(
            assignment_id
        )

        old_data = self._snapshot(
            assignment
        )

        if assignment.status in {
            self.STATUS_IN_PROGRESS,
            self.STATUS_COMPLETED,
        }:
            raise ValueError(
                (
                    "IN_PROGRESS or COMPLETED "
                    "assignments cannot be cancelled."
                )
            )

        assignment.status = (
            self.STATUS_CANCELLED
        )

        self.repository.update()

        self._record_history(
            assignment=assignment,
            action="CANCEL",
            old_data=old_data,
        )

        return assignment

    # ==========================================================
    # Audit history
    # ==========================================================

    def _snapshot(
        self,
        assignment,
    ):
        return (
            self.history_service
            .assignment_to_dict(
                assignment
            )
        )

    def _record_history(
        self,
        *,
        assignment,
        action,
        old_data,
        remark=None,
    ):
        return self.history_service.record(
            assignment=assignment,
            action=action,
            old_data=old_data,
            new_data=self._snapshot(
                assignment
            ),
            remark=remark,
        )

    # ==========================================================
    # Transaction
    # ==========================================================

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        if self._owns_session:
            self.session.close()

    # ==========================================================
    # Validation
    # ==========================================================

    def _require_assignment(
        self,
        assignment_id,
    ):
        assignment = self.get_assignment(
            assignment_id
        )

        if assignment is None:
            raise NotFoundError(
                (
                    "Production Assignment "
                    f"not found: {assignment_id}"
                )
            )

        return assignment

    def _require_editable(
        self,
        assignment_id,
    ):
        assignment = self._require_assignment(
            assignment_id
        )

        if assignment.status not in {
            self.STATUS_DRAFT,
            self.STATUS_ON_HOLD,
        }:
            raise ValueError(
                (
                    "Assignment cannot be edited "
                    f"when status is {assignment.status}."
                )
            )

        return assignment

    def _require_production_order(
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
        ) as error:
            raise ValueError(
                (
                    "Invalid Production Order ID: "
                    f"{production_order_id}"
                )
            ) from error

        production_order = (
            self.session
            .query(ProductionOrder)
            .filter(
                ProductionOrder.id
                == normalized_id
            )
            .first()
        )

        if production_order is None:
            raise NotFoundError(
                (
                    "Production Order not found: "
                    f"{normalized_id}"
                )
            )

        return production_order

    def _validate_resources(
        self,
        *,
        machine_code,
        employee_code,
    ):
        if machine_code:
            self._require_active_machine(
                machine_code
            )

        if employee_code:
            self._require_active_employee(
                employee_code
            )

    def _require_active_machine(
        self,
        machine_code,
    ):
        machine = (
            self.machine_service
            .get_machine(
                machine_code
            )
        )

        if machine is None:
            raise ValueError(
                (
                    "Machine does not exist: "
                    f"{machine_code}"
                )
            )

        status = self._normalize_upper(
            machine.status
        )

        if status not in {
            "ACTIVE",
            "RUNNING",
        }:
            raise ValueError(
                (
                    "Machine is not active: "
                    f"{machine_code}"
                )
            )

        return machine

    def _require_active_employee(
        self,
        employee_code,
    ):
        employee = (
            self.employee_service
            .get_employee(
                employee_code
            )
        )

        if employee is None:
            raise ValueError(
                (
                    "Employee does not exist: "
                    f"{employee_code}"
                )
            )

        if self._normalize_upper(
            employee.status
        ) != "ACTIVE":
            raise ValueError(
                (
                    "Employee is not active: "
                    f"{employee_code}"
                )
            )

        return employee

    @classmethod
    def _validate_assignment(
        cls,
        data,
        production_order,
    ):
        if data["production_order_id"] <= 0:
            raise ValueError(
                (
                    "Production Order ID must "
                    "be greater than zero."
                )
            )

        if (
            data["planned_start"] is not None
            and data["planned_finish"] is not None
            and data["planned_finish"]
            <= data["planned_start"]
        ):
            raise ValueError(
                (
                    "Planned Finish must be "
                    "after Planned Start."
                )
            )

        if (
            data["status"]
            not in cls.VALID_STATUSES
        ):
            raise ValueError(
                (
                    "Invalid Assignment Status: "
                    f"{data['status']}"
                )
            )

        del production_order

    def _validate_time_conflicts(
        self,
        data,
        exclude_assignment_id=None,
    ):
        if (
            data["planned_start"] is None
            or data["planned_finish"] is None
        ):
            return

        conflicts = (
            self.repository
            .find_time_conflicts(
                machine_code=data[
                    "machine_code"
                ],
                employee_code=data[
                    "employee_code"
                ],
                planned_start=data[
                    "planned_start"
                ],
                planned_finish=data[
                    "planned_finish"
                ],
                exclude_assignment_id=(
                    exclude_assignment_id
                ),
            )
        )

        if not conflicts:
            return

        conflict_messages = []

        for conflict in conflicts:
            resources = []

            if (
                data["machine_code"]
                and conflict.machine_code
                == data["machine_code"]
            ):
                resources.append(
                    (
                        "Machine "
                        f"{data['machine_code']}"
                    )
                )

            if (
                data["employee_code"]
                and conflict.employee_code
                == data["employee_code"]
            ):
                resources.append(
                    (
                        "Employee "
                        f"{data['employee_code']}"
                    )
                )

            conflict_messages.append(
                (
                    ", ".join(resources)
                    + f" conflicts with "
                    f"Assignment #{conflict.id}"
                )
            )

        raise ValueError(
            (
                "Assignment time conflict: "
                + "; ".join(
                    conflict_messages
                )
            )
        )

    # ==========================================================
    # Normalization
    # ==========================================================

    @classmethod
    def _normalize_data(
        cls,
        data,
    ):
        data = dict(
            data or {}
        )

        return {
            "production_order_id": int(
                data.get(
                    "production_order_id"
                )
            ),
            "machine_code": (
                cls._clean_optional_upper(
                    data.get(
                        "machine_code"
                    )
                )
            ),
            "employee_code": (
                cls._clean_optional_upper(
                    data.get(
                        "employee_code"
                    )
                )
            ),
            "shift": (
                cls._clean_optional_upper(
                    data.get(
                        "shift"
                    )
                )
            ),
            "planned_start": (
                cls._normalize_datetime(
                    data.get(
                        "planned_start"
                    )
                )
            ),
            "planned_finish": (
                cls._normalize_datetime(
                    data.get(
                        "planned_finish"
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
            "assigned_at": (
                cls._normalize_datetime(
                    data.get(
                        "assigned_at"
                    )
                )
            ),
            "released_at": (
                cls._normalize_datetime(
                    data.get(
                        "released_at"
                    )
                )
            ),
            "actual_start": (
                cls._normalize_datetime(
                    data.get(
                        "actual_start"
                    )
                )
            ),
            "actual_finish": (
                cls._normalize_datetime(
                    data.get(
                        "actual_finish"
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

    @classmethod
    def _normalize_status(
        cls,
        value,
    ):
        status = str(
            value
            or cls.STATUS_DRAFT
        ).strip().upper()

        if status not in cls.VALID_STATUSES:
            raise ValueError(
                (
                    "Invalid Assignment Status: "
                    f"{status}"
                )
            )

        return status

    @staticmethod
    def _normalize_code(
        value,
    ):
        return str(
            value or ""
        ).strip().upper()

    @staticmethod
    def _normalize_upper(
        value,
    ):
        return str(
            value or ""
        ).strip().upper()

    @staticmethod
    def _clean_optional_upper(
        value,
    ):
        text = str(
            value or ""
        ).strip().upper()

        return text or None

    @staticmethod
    def _clean_optional_text(
        value,
    ):
        text = str(
            value or ""
        ).strip()

        return text or None

    @staticmethod
    def _normalize_datetime(
        value,
    ):
        if value is None or value == "":
            return None

        if isinstance(
            value,
            datetime,
        ):
            return value

        if isinstance(
            value,
            date,
        ):
            return datetime.combine(
                value,
                datetime.min.time(),
            )

        text = str(
            value
        ).strip()

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
        ]

        for date_format in formats:
            try:
                return datetime.strptime(
                    text,
                    date_format,
                )
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(
                text
            )
        except ValueError as error:
            raise ValueError(
                (
                    "Invalid datetime value: "
                    f"{value}"
                )
            ) from error