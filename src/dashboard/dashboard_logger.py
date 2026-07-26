from __future__ import annotations

import logging


DASHBOARD_LOGGER_NAME = "factorymes.dashboard"

dashboard_logger = logging.getLogger(
    DASHBOARD_LOGGER_NAME
)


__all__ = [
    "DASHBOARD_LOGGER_NAME",
    "dashboard_logger",
]