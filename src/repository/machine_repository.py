from __future__ import annotations

from src.models.machine import Machine
from src.repository.base_repository import (
    BaseRepository,
)


class MachineRepository(
    BaseRepository
):
    """
    SQLAlchemy Repository cho Machine Master.
    """

    def __init__(
        self,
        session,
    ):
        super().__init__(
            session=session,
            model=Machine,
        )

    def get_by_code(
        self,
        machine_code,
    ):
        code = str(
            machine_code or ""
        ).strip().upper()

        if not code:
            return None

        return (
            self.session
            .query(Machine)
            .filter(
                Machine.machine_code == code
            )
            .first()
        )

    def exists(
        self,
        machine_code,
    ) -> bool:
        return (
            self.get_by_code(
                machine_code
            )
            is not None
        )