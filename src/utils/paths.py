from __future__ import annotations

import os
import sys
from pathlib import Path


APP_DIRECTORY_NAME = "FactoryMES"
DATA_DIRECTORY_ENV = "FACTORYMES_DATA_DIR"


def is_frozen() -> bool:
    """Trả về True khi ứng dụng đang chạy từ PyInstaller."""

    return bool(
        getattr(
            sys,
            "frozen",
            False,
        )
    )


def project_root() -> Path:
    """Thư mục gốc của source checkout."""

    return Path(__file__).resolve().parents[2]


def bundle_root() -> Path:
    """
    Thư mục chứa tài nguyên read-only của ứng dụng.

    PyInstaller đặt data files trong ``sys._MEIPASS``. Khi chạy
    source, tài nguyên nằm tại project root.
    """

    if is_frozen():
        temporary_root = getattr(
            sys,
            "_MEIPASS",
            None,
        )

        if temporary_root:
            return Path(
                temporary_root
            ).resolve()

        return (
            Path(sys.executable)
            .resolve()
            .parent
        )

    return project_root()


def config_path() -> Path:
    """Đường dẫn tới config được đóng gói cùng ứng dụng."""

    return (
        bundle_root()
        / "config"
        / "app.json"
    )


def asset_path(
    file_name: str,
) -> Path:
    """Đường dẫn tới một tài nguyên được bundle cùng ứng dụng."""

    return (
        bundle_root()
        / "assets"
        / str(file_name)
    )


def user_data_directory() -> Path:
    """Thư mục dữ liệu có quyền ghi của người dùng hiện tại."""

    override = str(
        os.environ.get(
            DATA_DIRECTORY_ENV,
            "",
        )
    ).strip()

    if override:
        return (
            Path(override)
            .expanduser()
            .resolve()
        )

    if os.name == "nt":
        local_app_data = str(
            os.environ.get(
                "LOCALAPPDATA",
                "",
            )
        ).strip()

        base_directory = (
            Path(local_app_data)
            if local_app_data
            else (
                Path.home()
                / "AppData"
                / "Local"
            )
        )

    else:
        xdg_data_home = str(
            os.environ.get(
                "XDG_DATA_HOME",
                "",
            )
        ).strip()

        base_directory = (
            Path(xdg_data_home)
            if xdg_data_home
            else (
                Path.home()
                / ".local"
                / "share"
            )
        )

    return (
        base_directory
        / APP_DIRECTORY_NAME
    )


def database_path() -> Path:
    """
    Đường dẫn database runtime.

    Chạy source vẫn dùng ``database/factory_mes.db`` để tương thích
    môi trường phát triển hiện tại. Bản đóng gói dùng thư mục dữ liệu
    người dùng và không ghi vào ``_internal`` của PyInstaller.
    """

    if (
        is_frozen()
        or os.environ.get(
            DATA_DIRECTORY_ENV
        )
    ):
        database_directory = (
            user_data_directory()
            / "database"
        )
    else:
        database_directory = (
            project_root()
            / "database"
        )

    return (
        database_directory
        / "factory_mes.db"
    )
