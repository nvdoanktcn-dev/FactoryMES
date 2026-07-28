from __future__ import annotations

import os
from unittest.mock import patch

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

# main.py phải được import trước PySide6 để six/dateutil được nạp
# trước khi Shiboken cài import hook.
from main import create_application
from PySide6.QtWidgets import QApplication

from src.config.app_config import APP_NAME, VERSION
from src.services.system_status_service import SystemStatusService
from src.ui.main_window import MainWindow
from src.ui.widgets.app_header import AppHeader
from src.utils.config import AppConfig


def get_application() -> QApplication:
    application = QApplication.instance()

    if application is None:
        application = QApplication([])

    return application


def test_shared_version_matches_json_configuration() -> None:
    config = AppConfig.load()

    assert VERSION == str(
        config.get("version")
    )
    assert APP_NAME == str(
        config.get("app_name")
    )
    assert VERSION == "0.5.6"


def test_service_and_qapplication_use_shared_version() -> None:
    config = AppConfig.load()
    application = create_application(config)

    assert (
        SystemStatusService.APP_VERSION
        == VERSION
    )
    assert (
        application.applicationVersion()
        == VERSION
    )
    assert (
        application.applicationName()
        == APP_NAME
    )


def test_app_header_displays_shared_version() -> None:
    get_application()

    header = AppHeader()

    try:
        labels = header.findChildren(
            type(header.clock)
        )
        texts = [
            label.text()
            for label in labels
        ]

        assert any(
            f"{APP_NAME} V{VERSION}"
            in text
            for text in texts
        )

    finally:
        header.close()
        header.deleteLater()


def test_main_window_displays_shared_version_without_loading_pages() -> None:
    get_application()

    # Không khởi tạo Dashboard hoặc service/database thật trong unit test.
    with (
        patch.object(
            MainWindow,
            "build_navigation",
        ),
        patch.object(
            MainWindow,
            "open_default_page",
        ),
    ):
        window = MainWindow()

    try:
        assert (
            window.windowTitle()
            == f"{APP_NAME} V{VERSION}"
        )
        assert (
            f"{APP_NAME} V{VERSION}"
            in window.title_label.text()
        )
        assert (
            f"{APP_NAME} Framework V{VERSION}"
            in window.footer_label.text()
        )

    finally:
        window.close()
        window.deleteLater()
