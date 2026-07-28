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


class TestProductionAssignmentTimeConflicts(
    DatabaseTestCase
):
    """Verify concurrent resource scheduling rules."""

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

        self.machine_1 = (
            MachineFactory.create_running(
                self.session,
                machine_code="BLTESTCONFLICT01",
                machine_name="Conflict CNC 01",
                machine_type="CNC",
            )
        )
        self.machine_2 = (
            MachineFactory.create_running(
                self.session,
                machine_code="BLTESTCONFLICT02",
                machine_name="Conflict CNC 02",
                machine_type="CNC",
            )
        )

        self.employee_1 = (
            EmployeeFactory.create_active(
                self.session,
                employee_code="EMP-CONFLICT-01",
                employee_name="Conflict Operator 01",
            )
        )
        self.employee_2 = (
            EmployeeFactory.create_active(
                self.session,
                employee_code="EMP-CONFLICT-02",
                employee_name="Conflict Operator 02",
            )
        )

    def _create_assignment(
        self,
        *,
        machine_code,
        employee_code,
        planned_start,
        planned_finish,
        status="DRAFT",
        remark=None,
    ):
        return self.service.create_assignment(
            {
                "production_order_id": (
                    self.production_order.id
                ),
                "machine_code": machine_code,
                "employee_code": employee_code,
                "shift": "DAY",
                "planned_start": planned_start,
                "planned_finish": planned_finish,
                "status": status,
                "assigned_at": None,
                "released_at": None,
                "actual_start": None,
                "actual_finish": None,
                "remark": remark,
            }
        )

    def test_concurrent_resource_scheduling_rules(
        self,
    ):
        # ======================================================
        # Scenario 1: overlapping use of the same machine
        # ======================================================
        machine_assignment = (
            self._create_assignment(
                machine_code=(
                    self.machine_1.machine_code
                ),
                employee_code=(
                    self.employee_1.employee_code
                ),
                planned_start=datetime(
                    2026, 8, 3, 8, 0
                ),
                planned_finish=datetime(
                    2026, 8, 3, 10, 0
                ),
                remark="Machine conflict baseline",
            )
        )

        self.session.flush()

        before_machine_conflict = len(
            self.service.get_all_assignments()
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                r"Assignment time conflict: "
                r"Machine BLTESTCONFLICT01 "
                r"conflicts with Assignment #"
            ),
        ):
            self._create_assignment(
                machine_code=(
                    self.machine_1.machine_code
                ),
                employee_code=(
                    self.employee_2.employee_code
                ),
                planned_start=datetime(
                    2026, 8, 3, 9, 0
                ),
                planned_finish=datetime(
                    2026, 8, 3, 11, 0
                ),
                remark="Must fail by machine",
            )

        self.assertEqual(
            len(
                self.service
                .get_all_assignments()
            ),
            before_machine_conflict,
        )

        persisted_machine_assignment = (
            self.service.get_assignment(
                machine_assignment.id
            )
        )

        self.assertEqual(
            persisted_machine_assignment.machine_code,
            self.machine_1.machine_code,
        )
        self.assertEqual(
            persisted_machine_assignment.employee_code,
            self.employee_1.employee_code,
        )

        # ======================================================
        # Scenario 2: overlapping use of the same employee
        # ======================================================
        employee_assignment = (
            self._create_assignment(
                machine_code=(
                    self.machine_1.machine_code
                ),
                employee_code=(
                    self.employee_1.employee_code
                ),
                planned_start=datetime(
                    2026, 8, 4, 8, 0
                ),
                planned_finish=datetime(
                    2026, 8, 4, 10, 0
                ),
                remark="Employee conflict baseline",
            )
        )

        self.session.flush()

        before_employee_conflict = len(
            self.service.get_all_assignments()
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                r"Assignment time conflict: "
                r"Employee EMP-CONFLICT-01 "
                r"conflicts with Assignment #"
            ),
        ):
            self._create_assignment(
                machine_code=(
                    self.machine_2.machine_code
                ),
                employee_code=(
                    self.employee_1.employee_code
                ),
                planned_start=datetime(
                    2026, 8, 4, 9, 30
                ),
                planned_finish=datetime(
                    2026, 8, 4, 11, 0
                ),
                remark="Must fail by employee",
            )

        self.assertEqual(
            len(
                self.service
                .get_all_assignments()
            ),
            before_employee_conflict,
        )

        persisted_employee_assignment = (
            self.service.get_assignment(
                employee_assignment.id
            )
        )

        self.assertEqual(
            persisted_employee_assignment.machine_code,
            self.machine_1.machine_code,
        )
        self.assertEqual(
            persisted_employee_assignment.employee_code,
            self.employee_1.employee_code,
        )

        # ======================================================
        # Scenario 3: touching time boundaries do not overlap
        # ======================================================
        boundary_first = self._create_assignment(
            machine_code=(
                self.machine_1.machine_code
            ),
            employee_code=(
                self.employee_1.employee_code
            ),
            planned_start=datetime(
                2026, 8, 5, 8, 0
            ),
            planned_finish=datetime(
                2026, 8, 5, 10, 0
            ),
            remark="Boundary first",
        )

        boundary_second = self._create_assignment(
            machine_code=(
                self.machine_1.machine_code
            ),
            employee_code=(
                self.employee_1.employee_code
            ),
            planned_start=datetime(
                2026, 8, 5, 10, 0
            ),
            planned_finish=datetime(
                2026, 8, 5, 12, 0
            ),
            remark="Boundary second",
        )

        self.assertIsNotNone(
            boundary_first.id
        )
        self.assertIsNotNone(
            boundary_second.id
        )

        # ======================================================
        # Scenario 4: different machine and employee may overlap
        # ======================================================
        independent_first = (
            self._create_assignment(
                machine_code=(
                    self.machine_1.machine_code
                ),
                employee_code=(
                    self.employee_1.employee_code
                ),
                planned_start=datetime(
                    2026, 8, 6, 8, 0
                ),
                planned_finish=datetime(
                    2026, 8, 6, 12, 0
                ),
                remark="Independent first",
            )
        )

        independent_second = (
            self._create_assignment(
                machine_code=(
                    self.machine_2.machine_code
                ),
                employee_code=(
                    self.employee_2.employee_code
                ),
                planned_start=datetime(
                    2026, 8, 6, 9, 0
                ),
                planned_finish=datetime(
                    2026, 8, 6, 11, 0
                ),
                remark="Independent second",
            )
        )

        self.assertIsNotNone(
            independent_first.id
        )
        self.assertIsNotNone(
            independent_second.id
        )

        # ======================================================
        # Scenario 5: completed assignments release resources
        # ======================================================
        completed_assignment = (
            self._create_assignment(
                machine_code=(
                    self.machine_1.machine_code
                ),
                employee_code=(
                    self.employee_1.employee_code
                ),
                planned_start=datetime(
                    2026, 8, 7, 8, 0
                ),
                planned_finish=datetime(
                    2026, 8, 7, 12, 0
                ),
                status="COMPLETED",
                remark="Completed resource booking",
            )
        )

        replacement_assignment = (
            self._create_assignment(
                machine_code=(
                    self.machine_1.machine_code
                ),
                employee_code=(
                    self.employee_1.employee_code
                ),
                planned_start=datetime(
                    2026, 8, 7, 9, 0
                ),
                planned_finish=datetime(
                    2026, 8, 7, 11, 0
                ),
                remark=(
                    "Allowed because previous "
                    "assignment is completed"
                ),
            )
        )

        self.session.flush()

        self.assertEqual(
            completed_assignment.status,
            "COMPLETED",
        )
        self.assertEqual(
            replacement_assignment.status,
            "DRAFT",
        )

        persisted_ids = {
            assignment.id
            for assignment
            in self.service.get_all_assignments()
        }

        expected_assignments = {
            machine_assignment.id,
            employee_assignment.id,
            boundary_first.id,
            boundary_second.id,
            independent_first.id,
            independent_second.id,
            completed_assignment.id,
            replacement_assignment.id,
        }

        self.assertTrue(
            expected_assignments.issubset(
                persisted_ids
            )
        )