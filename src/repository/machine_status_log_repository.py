from __future__ import annotations

from src.models.machine_status_log import (
    MachineStatusLog,
)
from src.repository.base_repository import (
    BaseRepository,
)


class MachineStatusLogRepository(
    BaseRepository
):
    def __init__(
        self,
        session,
    ):
        super().__init__(
            session=session,
            model=MachineStatusLog,
        )

    def get_by_machine_id(
        self,
        machine_id,
    ):
        return (
            self.session
            .query(MachineStatusLog)
            .filter(
                MachineStatusLog.machine_id
                == int(machine_id)
            )
            .order_by(
                MachineStatusLog.changed_at.desc(),
                MachineStatusLog.id.desc(),
            )
            .all()
        )

    def get_by_machine_code(
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
            .query(MachineStatusLog)
            .filter(
                MachineStatusLog.machine_code
                == code
            )
            .order_by(
                MachineStatusLog.changed_at.desc(),
                MachineStatusLog.id.desc(),
            )
            .all()
        )

    def get_latest_by_machine_code(
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
            .query(MachineStatusLog)
            .filter(
                MachineStatusLog.machine_code
                == code
            )
            .order_by(
                MachineStatusLog.changed_at.desc(),
                MachineStatusLog.id.desc(),
            )
            .first()
        )
