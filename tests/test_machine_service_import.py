from __future__ import annotations

import uuid

from src.models.machine import Machine
from src.services.machine_service import MachineService
from tests.base.base_database_test import BaseDatabaseTest


class TestMachineServiceImport(BaseDatabaseTest):

    def setUp(self):
        super().setUp()

        self.machine_code = (
            f"BLTEST{uuid.uuid4().hex[:8].upper()}"
        )

        self.service = MachineService(
            session=self.session,
        )

    def tearDown(self):
        try:
            self.session.rollback()

            (
                self.session.query(Machine)
                .filter(Machine.machine_code == self.machine_code)
                .delete(synchronize_session=False)
            )

            self.session.commit()
        finally:
            super().tearDown()

    def test_save_machine_then_rollback(self):
        machine, action = self.service.save_machine(
            {
                "machine_code": self.machine_code,
                "machine_name": "Test CNC Machine",
                "machine_type": "CNC",
                "line": "CNC",
                "location": "Factory 1",
                "brand": "Brother",
                "model": "S700",
                "serial_number": f"SN-{uuid.uuid4().hex[:8]}",
                "status": "RUNNING",
            }
        )

        self.assertIsNotNone(machine)
        self.assertEqual(machine.machine_code, self.machine_code)
        self.assertEqual(action, "created")

        self.session.rollback()

        saved_machine = (
            self.session.query(Machine)
            .filter(Machine.machine_code == self.machine_code)
            .one_or_none()
        )

        self.assertIsNone(saved_machine)

    def test_valid_machine_code_conventions(self):
        valid_cases = [
            (
                f"BL{uuid.uuid4().hex[:8].upper()}",
                "CNC",
            ),
            (
                "BR01",
                "ROBOT",
            ),
            (
                f"ASK{int(uuid.uuid4().hex[:6], 16)}",
                "ROBOT",
            ),
            (
                f"BRASK{uuid.uuid4().hex[:6].upper()}",
                "ROBOT",
            ),
        ]

        for machine_code, machine_type in valid_cases:
            with self.subTest(
                machine_code=machine_code,
                machine_type=machine_type,
            ):
                machine = self.service.create_machine(
                    {
                        "machine_code": machine_code,
                        "machine_name": (
                            f"Test {machine_type} Machine"
                        ),
                        "machine_type": machine_type,
                        "status": "RUNNING",
                    }
                )

                self.assertEqual(
                    machine.machine_code,
                    machine_code,
                )
                self.assertEqual(
                    machine.machine_type,
                    machine_type,
                )

        self.session.rollback()

    def test_invalid_machine_code_conventions(self):
        invalid_cases = [
            (
                "CNC-001",
                "CNC",
            ),
            (
                "BL01",
                "ROBOT",
            ),
            (
                "BR01",
                "CNC",
            ),
            (
                "BR12",
                "ROBOT",
            ),
            (
                "ASK",
                "ROBOT",
            ),
            (
                "ASK-A",
                "ROBOT",
            ),
            (
                "BRASK",
                "ROBOT",
            ),
        ]

        for machine_code, machine_type in invalid_cases:
            with self.subTest(
                machine_code=machine_code,
                machine_type=machine_type,
            ):
                with self.assertRaises(ValueError):
                    self.service.create_machine(
                        {
                            "machine_code": machine_code,
                            "machine_name": "Invalid Machine",
                            "machine_type": machine_type,
                            "status": "RUNNING",
                        }
                    )
