from __future__ import annotations

import sys
import traceback
from typing import NoReturn

import six  # noqa: F401
from dateutil import parser as _dateutil_parser  # noqa: F401
from dateutil import rrule as _dateutil_rrule  # noqa: F401

import matplotlib

matplotlib.use("qtagg")

from matplotlib.backends.backend_qtagg import (  # noqa: E402, F401
    FigureCanvasQTAgg as _FigureCanvasQTAgg,
)
from PySide6.QtCore import qInstallMessageHandler, qVersion  # noqa: E402
from PySide6.QtGui import QFont  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from src.database.base import Base  # noqa: E402
from src.database.database import engine  # noqa: E402
from src.database.session import close_all_sessions  # noqa: E402

import src.models  # noqa: E402, F401

from src.ui.main_window import MainWindow  # noqa: E402
from src.ui.theme.theme_manager import ThemeManager  # noqa: E402
from src.utils.config import AppConfig  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402


logger = get_logger(__name__)


def qt_message_handler(mode, context, message: str) -> None:
    """Ghi lại cảnh báo Qt để hỗ trợ chẩn đoán lỗi giao diện."""

    del context

    if "QFont::setPointSize" in message:
        stack_trace = "".join(traceback.format_stack())

        logger.warning(
            "Qt font warning detected: %s\n%s",
            message,
            stack_trace,
        )
        return

    mode_name = getattr(mode, "name", str(mode))

    logger.debug(
        "Qt message [%s]: %s",
        mode_name,
        message,
    )


def initialize_database() -> None:
    """Khởi tạo các bảng cơ sở dữ liệu chưa tồn tại."""

    logger.info("Initializing database schema...")

    Base.metadata.create_all(
        bind=engine,
    )

    logger.info("Database schema is ready.")


def create_application(config: AppConfig) -> QApplication:
    """Tạo và cấu hình QApplication dùng chung."""

    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv)

    version = config.get("version") or "unknown"

    app.setApplicationName("FactoryMES")
    app.setOrganizationName("FactoryMES")
    app.setApplicationVersion(str(version))

    app.setFont(
        QFont(
            "Segoe UI",
            10,
        )
    )

    ThemeManager.apply_light_theme(app)

    return app


def run_application(config: AppConfig) -> int:
    """Tạo cửa sổ chính và chạy vòng lặp sự kiện Qt."""

    app = create_application(config)

    app.aboutToQuit.connect(
        close_all_sessions
    )

    window = MainWindow()
    window.show()

    exit_code = app.exec()

    logger.info(
        "Application closed with exit code %s.",
        exit_code,
    )

    return int(exit_code)


def main() -> NoReturn:
    """Điểm vào chính của ứng dụng."""

    try:
        qInstallMessageHandler(
            qt_message_handler
        )

        config = AppConfig.load()
        version = config.get("version") or "unknown"

        logger.info("FactoryMES starting...")
        logger.info("Version: %s", version)
        logger.info(
            "Python: %s",
            sys.version.replace("\n", " "),
        )
        logger.info("Qt: %s", qVersion())

        initialize_database()

        exit_code = run_application(config)

    except Exception:
        logger.exception(
            "FactoryMES terminated because of an unhandled error."
        )
        raise

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
