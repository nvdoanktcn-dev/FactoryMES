from __future__ import annotations

from src.models.robot_operation_log import RobotOperationLog
from src.repository.base_repository import BaseRepository


class RobotOperationLogRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(
            session=session,
            model=RobotOperationLog,
        )

    def get_by_id(self, log_id):
        try:
            normalized_id = int(log_id)
        except (TypeError, ValueError):
            return None

        return (
            self.session
            .query(RobotOperationLog)
            .filter(
                RobotOperationLog.id == normalized_id
            )
            .first()
        )

    def get_all(self):
        return (
            self.session
            .query(RobotOperationLog)
            .order_by(
                RobotOperationLog.log_date.desc().nullslast(),
                RobotOperationLog.id.desc(),
            )
            .all()
        )
