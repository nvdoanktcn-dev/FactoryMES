from __future__ import annotations

from src.models.cnc_production_log import CNCProductionLog
from src.repository.base_repository import BaseRepository


class CNCProductionLogRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(
            session=session,
            model=CNCProductionLog,
        )

    def get_by_id(self, log_id):
        try:
            normalized_id = int(log_id)
        except (TypeError, ValueError):
            return None

        return (
            self.session
            .query(CNCProductionLog)
            .filter(
                CNCProductionLog.id == normalized_id
            )
            .first()
        )

    def get_all(self):
        return (
            self.session
            .query(CNCProductionLog)
            .order_by(
                CNCProductionLog.log_date.desc().nullslast(),
                CNCProductionLog.id.desc(),
            )
            .all()
        )
