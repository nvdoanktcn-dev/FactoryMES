from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIRECTORY = Path("logs")
LOG_FILE = LOG_DIRECTORY / "factorymes.log"

DEFAULT_LOG_LEVEL = logging.INFO

_LOGGING_CONFIGURED = False


def configure_logging(
    level: int = DEFAULT_LOG_LEVEL,
) -> None:
    """
    Cấu hình logging dùng chung cho FactoryMES.

    Chức năng:
    - Ghi log ra PowerShell.
    - Ghi log ra logs/factorymes.log.
    - Tự xoay file khi log vượt 5 MB.
    - Giữ tối đa 5 file backup.
    """

    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED:
        return

    LOG_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    formatter = logging.Formatter(
        (
            "%(asctime)s | "
            "%(levelname)-8s | "
            "%(name)s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(
        formatter
    )

    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )

    file_handler.setLevel(level)
    file_handler.setFormatter(
        formatter
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    root_logger.addHandler(
        console_handler
    )

    root_logger.addHandler(
        file_handler
    )

    _LOGGING_CONFIGURED = True


def get_logger(
    name: str,
) -> logging.Logger:
    configure_logging()

    return logging.getLogger(
        name
    )