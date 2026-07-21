from datetime import datetime

from sqlalchemy import text

from src.database.session import get_session


class SystemStatusService:
    """
    Service kiểm tra trạng thái hệ thống.

    Không phụ thuộc UI.
    """

    APP_VERSION = "3.0.0"

    def __init__(
        self,
        session=None,
    ):
        self.session = session or get_session()

    # ==========================================================
    # Public API
    # ==========================================================

    def build_status(self):
        now = datetime.now()

        database_status = (
            self.check_database()
        )

        current_shift = (
            self.resolve_current_shift(now)
        )

        return {
            "database": database_status,

            "analytics": {
                "status": "ONLINE",
                "message": "Analytics service ready.",
            },

            "dashboard": {
                "status": "ONLINE",
                "message": "Dashboard ready.",
            },

            "plc": {
                "status": "NOT_CONFIGURED",
                "message": (
                    "PLC / OPC-UA is not configured."
                ),
            },

            "last_check": now,

            "current_shift": current_shift,

            "version": self.APP_VERSION,
        }

    # ==========================================================
    # Database
    # ==========================================================

    def check_database(self):
        try:
            self.session.execute(
                text("SELECT 1")
            )

            return {
                "status": "ONLINE",
                "message": "Database connection OK.",
            }

        except Exception as error:
            try:
                self.session.rollback()
            except Exception:
                pass

            return {
                "status": "OFFLINE",
                "message": str(error),
            }

    # ==========================================================
    # Shift
    # ==========================================================

    @staticmethod
    def resolve_current_shift(
        current_datetime,
    ):
        """
        Day:
            08:00 <= time < 20:00

        Night:
            20:00 <= time
            hoặc time < 08:00
        """
        current_hour = (
            current_datetime.hour
        )

        if 8 <= current_hour < 20:
            return "DAY"

        return "NIGHT"