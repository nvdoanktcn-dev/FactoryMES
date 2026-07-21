import sys
import traceback

# Nạp các dependency của Matplotlib trước khi tải toàn bộ model/UI.
import six
from dateutil import parser as _dateutil_parser
from dateutil import rrule as _dateutil_rrule

import matplotlib

matplotlib.use("qtagg")

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as _FigureCanvasQTAgg,
)

from PySide6.QtCore import qInstallMessageHandler
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from src.database.base import Base
from src.database.database import engine

# Đăng ký toàn bộ SQLAlchemy model.
import src.models

from src.ui.main_window import MainWindow
from src.ui.theme.theme_manager import ThemeManager
from src.utils.config import AppConfig
from src.utils.logger import get_logger


def qt_message_handler(
    mode,
    context,
    message,
):
    """
    Bắt các warning của Qt để hỗ trợ debug.
    """

    del mode
    del context

    if "QFont::setPointSize" in message:

        print("\n" + "=" * 60)
        print("Qt Font Warning")
        print("=" * 60)

        print(message)

        traceback.print_stack()

        print("=" * 60)

        sys.exit(1)


qInstallMessageHandler(
    qt_message_handler
)

logger = get_logger(__name__)


def main():
    config = AppConfig.load()

    logger.info("FactoryMES starting...")
    logger.info(
        "Version: %s",
        config.get("version"),
    )

    Base.metadata.create_all(
        bind=engine
    )

    app = QApplication(
        sys.argv
    )

    # Font mặc định cho toàn bộ ứng dụng
    app.setFont(
        QFont(
            "Segoe UI",
            10,
        )
    )

    ThemeManager.apply_light_theme(
        app
    )

    window = MainWindow()
    window.show()

    exit_code = app.exec()

    logger.info(
        "Application closed."
    )

    sys.exit(
        exit_code
    )


if __name__ == "__main__":
    main()