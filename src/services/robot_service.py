from __future__ import annotations

from sqlalchemy.orm import Session

from src.framework.exception import DuplicateError, NotFoundError
from src.framework.validator import BaseValidator
from src.models.robot import Robot
from src.repository.robot_repository import RobotRepository
from src.services.base_service import SessionOwnedService


class RobotService(SessionOwnedService):
    """
    Service quản lý danh mục Robot.
    """

    STATUS_ACTIVE = "ACTIVE"
    STATUS_MAINTENANCE = "MAINTENANCE"
    STATUS_STOPPED = "STOPPED"

    VALID_STATUS = {
        STATUS_ACTIVE,
        STATUS_MAINTENANCE,
        STATUS_STOPPED,
    }

    def __init__(
        self,
        session: Session | None = None,
        repository: RobotRepository | None = None,
    ) -> None:
        if repository is not None:
            super().__init__(
                session=getattr(repository, "session", None)
            )
            self._owns_session = False
            self.repository = repository
            return

        super().__init__(session=session)

        self.repository = RobotRepository(
            self.require_session()
        )

    # ==========================================================
    # Query
    # ==========================================================

    def get_all_robots(self):
        return self.repository.get_all()

    def get_robot(self, robot_code):
        code = self._normalize_code(robot_code)

        if not code:
            return None

        return self.repository.get_by_code(code)

    def get_by_code(self, robot_code):
        return self.get_robot(robot_code)

    def search_robots(self, keyword):
        robots = self.get_all_robots()

        text = str(keyword or "").strip().lower()

        if not text:
            return robots

        return [
            robot
            for robot in robots
            if (
                text in str(robot.robot_code or "").lower()
                or text in str(robot.robot_name or "").lower()
                or text in str(robot.robot_type or "").lower()
                or text in str(robot.area or "").lower()
                or text in str(robot.station or "").lower()
                or text in str(robot.status or "").lower()
            )
        ]

    # ==========================================================
    # Create
    # ==========================================================

    def create_robot(self, data):
        normalized = self._normalize_data(data)

        robot_code = normalized["robot_code"]
        robot_name = normalized["robot_name"]

        self._validate_robot(
            robot_code=robot_code,
            robot_name=robot_name,
        )

        if self.repository.exists(robot_code):
            raise DuplicateError(
                f"Robot already exists: {robot_code}"
            )

        robot = Robot(**normalized)

        self.log_info(f"Create Robot: {robot_code}")

        return self.repository.add(robot)

    # ==========================================================
    # Update
    # ==========================================================

    def update_robot(self, robot_code, data):
        code = self._normalize_code(robot_code)

        robot = self.repository.get_by_code(code)

        if robot is None:
            raise NotFoundError(f"Robot not found: {code}")

        normalized = self._normalize_data(
            {**dict(data or {}), "robot_code": code}
        )

        self._validate_robot(
            robot_code=code,
            robot_name=normalized["robot_name"],
        )

        robot.robot_name = normalized["robot_name"]
        robot.robot_type = normalized["robot_type"]
        robot.area = normalized["area"]
        robot.station = normalized["station"]
        robot.status = normalized["status"]
        robot.remark = normalized["remark"]

        self.log_info(f"Update Robot: {code}")

        self.repository.update()

        return robot

    # ==========================================================
    # Deactivate
    # ==========================================================

    def delete_robot(self, robot_code):
        code = self._normalize_code(robot_code)

        robot = self.repository.get_by_code(code)

        if robot is None:
            raise NotFoundError(f"Robot not found: {code}")

        robot.status = self.STATUS_STOPPED

        self.log_warning(f"Stopped Robot: {code}")

        self.repository.update()

        return robot

    # ==========================================================
    # Validation and normalization
    # ==========================================================

    @staticmethod
    def _validate_robot(robot_code, robot_name):
        BaseValidator.required(robot_code, "Robot Code")
        BaseValidator.required(robot_name, "Robot Name")
        BaseValidator.max_length(robot_code, "Robot Code", 30)
        BaseValidator.max_length(robot_name, "Robot Name", 100)

    @classmethod
    def _normalize_data(cls, data):
        data = dict(data or {})

        return {
            "robot_code": cls._normalize_code(
                data.get("robot_code")
            ),
            "robot_name": cls._clean_text(
                data.get("robot_name")
            ),
            "robot_type": cls._clean_optional_text(
                data.get("robot_type")
            ),
            "area": cls._clean_optional_text(
                data.get("area")
            ),
            "station": cls._clean_optional_text(
                data.get("station")
            ),
            "status": cls._normalize_status(
                data.get("status")
            ),
            "remark": cls._clean_optional_text(
                data.get("remark")
            ),
        }

    @staticmethod
    def _normalize_code(value):
        return str(value or "").strip().upper()

    @staticmethod
    def _clean_text(value):
        return str(value or "").strip()

    @staticmethod
    def _clean_optional_text(value):
        text = str(value or "").strip()
        return text or None

    @classmethod
    def _normalize_status(cls, value):
        status = str(value or cls.STATUS_ACTIVE).strip().upper()

        if status not in cls.VALID_STATUS:
            raise ValueError(f"Invalid Robot Status: {status}")

        return status
