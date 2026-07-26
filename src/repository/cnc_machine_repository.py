from __future__ import annotations

from src.models.cnc_machine import CNCMachine
from src.repository.base_repository import BaseRepository


class CNCMachineRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(
            session=session,
            model=CNCMachine,
        )

    def get_by_code(self, machine_code):
        code = str(machine_code or "").strip().upper()

        if not code:
            return None

        return (
            self.session
            .query(CNCMachine)
            .filter(
                CNCMachine.machine_code == code
            )
            .first()
        )

    def exists(self, machine_code) -> bool:
        return self.get_by_code(machine_code) is not None
