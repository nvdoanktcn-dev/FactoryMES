from __future__ import annotations

import uuid

from src.models.machine import Machine
from src.services.machine_service import MachineService
from tests.base.base_database_test import BaseDatabaseTest


class TestMachineServiceImport(BaseDatabaseTest):

    def setUp(self):
        super().setUp()

        self.machine_code = f"TEST-BL-{uuid.uuid4().hex[:8].upper()}"

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