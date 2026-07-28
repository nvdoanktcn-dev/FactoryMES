from __future__ import annotations

from datetime import datetime

from src.services.production_assignment_service import (
    ProductionAssignmentService,
)
from tests.base.database_test_case import DatabaseTestCase
from tests.factories.employee_factory import EmployeeFactory
from tests.factories.machine_factory import MachineFactory
from tests.factories.production_assignment_factory import (
    ProductionAssignmentFactory,
)


class TestProductionAssignmentUpdateConflicts(
    DatabaseTestCase
):
    """Verify conflict protection on assignment edits."""

    def setUp(self):
        super().setUp()

        self.service = ProductionAssignmentService(
            session=self.session
        )

        self.production_order = (
            ProductionAssignmentFactory
            .get_production_order(
                self.session
            )
        )

        self.machine_1 = MachineFactory.create_running(
            self.session,
            machine_code="BLTESTUPDATE01",
            machine_name="Update Conflict CNC 01",
            machine_type="CNC",
        )
        self.machine_2 = MachineFactory.create_running(
            self.session,
            machine_code="BLTESTUPDATE02",
            machine_name="Update Conflict CNC 02",
            machine_type="CNC",
        )

        self.employee_1 = EmployeeFactory.create_active(
            self.session,
            employee_code="EMP-UPDATE-01",
            employee_name="Update Operator 01",
        )
        self.employee_2 = EmployeeFactory.create_active(
            self.session,
            employee_code="EMP-UPDATE-02",
            employee_name="Update Operator 02",
        )

    def _create_assignment(
        self,
        *,
        machine_code,
        employee_code,
        planned_start,
        planned_finish,
        status="DRAFT",
        remark,
    ):
        assignment = (
            ProductionAssignmentFactory.create(
                self.session,
                production_order=self.production_order,
                machine_code=machine_code,
                employee_code=employee_code,
                shift="DAY",
                planned_start=planned_start,
                planned_finish=planned_finish,
                status=status,
                remark=remark,
            )
        )

        self.session.flush()

        return assignment

    @staticmethod
    def _update_data(
        assignment,
        *,
        machine_code=None,
        employee_code=None,
        planned_start=None,
        planned_finish=None,
        remark=None,
    ):
        """
        update_assignment() normalizes the submitted payload rather than
        applying a partial patch, so submit every editable field.
        """
        return {
            "machine_code": (
                assignment.machine_code
                if machine_code is None
                else machine_code
            ),
            "employee_code": (
                assignment.employee_code
                if employee_code is None
                else employee_code
            ),
            "shift": assignment.shift,
            "planned_start": (
                assignment.planned_start
                if planned_start is None
                else planned_start
            ),
            "planned_finish": (
                assignment.planned_finish
                if planned_finish is None
                else planned_finish
            ),
            "remark": (
                assignment.remark
                if remark is None
                else remark
            ),
        }

    def test_update_conflict_guards(
        self,
    ):
        # ======================================================
        # Baseline assignments
        # ======================================================
        assignment_a = self._create_assignment(
            machine_code=self.machine_1.machine_code,
            employee_code=self.employee_1.employee_code,
            planned_start=datetime(
                2026, 8, 10, 8, 0
            ),
            planned_finish=datetime(
                2026, 8, 10, 12, 0
            ),
            remark="Baseline assignment A",
        )

        assignment_b = self._create_assignment(
            machine_code=self.machine_2.machine_code,
            employee_code=self.employee_2.employee_code,
            planned_start=datetime(
                2026, 8, 10, 13, 0
            ),
            planned_finish=datetime(
                2026, 8, 10, 17, 0
            ),
            remark="Baseline assignment B",
        )

        assignment_b_id = assignment_b.id

        # ======================================================
        # Scenario 1: update rejects machine conflict
        # ======================================================
        with self.assertRaisesRegex(
            ValueError,
            (
                r"Assignment time conflict: "
                r"Machine BLTESTUPDATE01 "
                r"conflicts with Assignment #"
            ),
        ):
            self.service.update_assignment(
                assignment_b_id,
                self._update_data(
                    assignment_b,
                    machine_code=(
                        self.machine_1.machine_code
                    ),
                    planned_start=datetime(
                        2026, 8, 10, 9, 0
                    ),
                    planned_finish=datetime(
                        2026, 8, 10, 11, 0
                    ),
                    remark=(
                        "Must fail by machine conflict"
                    ),
                ),
            )

        self.session.expire_all()

        persisted_b = self.service.get_assignment(
            assignment_b_id
        )

        self.assertEqual(
            persisted_b.machine_code,
            self.machine_2.machine_code,
        )
        self.assertEqual(
            persisted_b.employee_code,
            self.employee_2.employee_code,
        )
        self.assertEqual(
            persisted_b.planned_start,
            datetime(2026, 8, 10, 13, 0),
        )
        self.assertEqual(
            persisted_b.planned_finish,
            datetime(2026, 8, 10, 17, 0),
        )
        self.assertEqual(
            persisted_b.remark,
            "Baseline assignment B",
        )

        # ======================================================
        # Scenario 2: update rejects employee conflict
        # ======================================================
        with self.assertRaisesRegex(
            ValueError,
            (
                r"Assignment time conflict: "
                r"Employee EMP-UPDATE-01 "
                r"conflicts with Assignment #"
            ),
        ):
            self.service.update_assignment(
                assignment_b_id,
                self._update_data(
                    persisted_b,
                    employee_code=(
                        self.employee_1.employee_code
                    ),
                    planned_start=datetime(
                        2026, 8, 10, 9, 30
                    ),
                    planned_finish=datetime(
                        2026, 8, 10, 11, 30
                    ),
                    remark=(
                        "Must fail by employee conflict"
                    ),
                ),
            )

        self.session.expire_all()

        persisted_b = self.service.get_assignment(
            assignment_b_id
        )

        self.assertEqual(
            persisted_b.machine_code,
            self.machine_2.machine_code,
        )
        self.assertEqual(
            persisted_b.employee_code,
            self.employee_2.employee_code,
        )
        self.assertEqual(
            persisted_b.planned_start,
            datetime(2026, 8, 10, 13, 0),
        )
        self.assertEqual(
            persisted_b.planned_finish,
            datetime(2026, 8, 10, 17, 0),
        )
        self.assertEqual(
            persisted_b.remark,
            "Baseline assignment B",
        )

        # ======================================================
        # Scenario 3: touching boundary is allowed
        # ======================================================
        updated_b = self.service.update_assignment(
            assignment_b_id,
            self._update_data(
                persisted_b,
                machine_code=self.machine_1.machine_code,
                employee_code=(
                    self.employee_1.employee_code
                ),
                planned_start=datetime(
                    2026, 8, 10, 12, 0
                ),
                planned_finish=datetime(
                    2026, 8, 10, 16, 0
                ),
                remark="Boundary update succeeds",
            ),
        )

        self.session.flush()

        self.assertEqual(
            updated_b.machine_code,
            self.machine_1.machine_code,
        )
        self.assertEqual(
            updated_b.employee_code,
            self.employee_1.employee_code,
        )
        self.assertEqual(
            updated_b.planned_start,
            datetime(2026, 8, 10, 12, 0),
        )
        self.assertEqual(
            updated_b.planned_finish,
            datetime(2026, 8, 10, 16, 0),
        )
        self.assertEqual(
            updated_b.remark,
            "Boundary update succeeds",
        )

        # Updating without changing the interval must not conflict
        # with the assignment itself.
        self_update = self.service.update_assignment(
            assignment_b_id,
            self._update_data(
                updated_b,
                remark="Self exclusion confirmed",
            ),
        )

        self.assertEqual(
            self_update.remark,
            "Self exclusion confirmed",
        )

        # ======================================================
        # Scenario 4: assign_machine rejects occupied machine
        # ======================================================
        machine_source = self._create_assignment(
            machine_code=self.machine_1.machine_code,
            employee_code=self.employee_1.employee_code,
            planned_start=datetime(
                2026, 8, 11, 8, 0
            ),
            planned_finish=datetime(
                2026, 8, 11, 12, 0
            ),
            remark="Machine assignment source",
        )

        machine_target = self._create_assignment(
            machine_code=self.machine_2.machine_code,
            employee_code=self.employee_2.employee_code,
            planned_start=datetime(
                2026, 8, 11, 8, 0
            ),
            planned_finish=datetime(
                2026, 8, 11, 12, 0
            ),
            remark="Machine assignment target",
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                r"Assignment time conflict: "
                r"Machine BLTESTUPDATE01 "
                r"conflicts with Assignment #"
            ),
        ):
            self.service.assign_machine(
                machine_target.id,
                self.machine_1.machine_code,
            )

        self.session.expire_all()

        persisted_machine_target = (
            self.service.get_assignment(
                machine_target.id
            )
        )

        self.assertEqual(
            persisted_machine_target.machine_code,
            self.machine_2.machine_code,
        )
        self.assertEqual(
            machine_source.machine_code,
            self.machine_1.machine_code,
        )

        # Reassigning the same machine to the same assignment must
        # not detect the assignment as its own conflict.
        same_machine = self.service.assign_machine(
            machine_source.id,
            self.machine_1.machine_code,
        )

        self.assertEqual(
            same_machine.machine_code,
            self.machine_1.machine_code,
        )

        # ======================================================
        # Scenario 5: assign_employee rejects occupied employee
        # ======================================================
        employee_source = self._create_assignment(
            machine_code=self.machine_1.machine_code,
            employee_code=self.employee_1.employee_code,
            planned_start=datetime(
                2026, 8, 12, 8, 0
            ),
            planned_finish=datetime(
                2026, 8, 12, 12, 0
            ),
            remark="Employee assignment source",
        )

        employee_target = self._create_assignment(
            machine_code=self.machine_2.machine_code,
            employee_code=self.employee_2.employee_code,
            planned_start=datetime(
                2026, 8, 12, 8, 0
            ),
            planned_finish=datetime(
                2026, 8, 12, 12, 0
            ),
            remark="Employee assignment target",
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                r"Assignment time conflict: "
                r"Employee EMP-UPDATE-01 "
                r"conflicts with Assignment #"
            ),
        ):
            self.service.assign_employee(
                employee_target.id,
                self.employee_1.employee_code,
            )

        self.session.expire_all()

        persisted_employee_target = (
            self.service.get_assignment(
                employee_target.id
            )
        )

        self.assertEqual(
            persisted_employee_target.employee_code,
            self.employee_2.employee_code,
        )
        self.assertEqual(
            employee_source.employee_code,
            self.employee_1.employee_code,
        )

        # Reassigning the current employee must also exclude self.
        same_employee = self.service.assign_employee(
            employee_source.id,
            self.employee_1.employee_code,
        )

        self.assertEqual(
            same_employee.employee_code,
            self.employee_1.employee_code,
        )

        # ======================================================
        # Final persistence checks
        # ======================================================
        self.session.flush()

        persisted_a = self.service.get_assignment(
            assignment_a.id
        )
        persisted_b = self.service.get_assignment(
            assignment_b_id
        )

        self.assertEqual(
            persisted_a.remark,
            "Baseline assignment A",
        )
        self.assertEqual(
            persisted_b.remark,
            "Self exclusion confirmed",
        )