from __future__ import annotations

from uuid import uuid4


class MachineFactory:

    @staticmethod
    def create(**kwargs):
        data = {
            "machine_code": f"TEST-{uuid4().hex[:8]}",
            "machine_name": "Test Machine",
            "machine_type": "CNC",
            "line": "CNC",
            "location": "Factory 1",
            "brand": "Brother",
            "model": "S700",
            "serial_number": uuid4().hex,
            "status": "RUNNING",
        }

        data.update(kwargs)
        return data