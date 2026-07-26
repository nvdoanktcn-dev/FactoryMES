from __future__ import annotations

from src.models.robot import Robot
from src.repository.base_repository import BaseRepository


class RobotRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(
            session=session,
            model=Robot,
        )

    def get_by_code(self, robot_code):
        code = str(robot_code or "").strip().upper()

        if not code:
            return None

        return (
            self.session
            .query(Robot)
            .filter(
                Robot.robot_code == code
            )
            .first()
        )

    def exists(self, robot_code) -> bool:
        return self.get_by_code(robot_code) is not None
