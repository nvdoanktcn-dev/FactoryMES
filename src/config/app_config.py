from __future__ import annotations

from src.utils.config import AppConfig


_CONFIG = AppConfig.load()

APP_NAME = str(
    _CONFIG.get("app_name")
    or "FactoryMES"
)

VERSION = str(
    _CONFIG.get("version")
    or "unknown"
)

COMPANY = "Your Company"

DATABASE = str(
    _CONFIG.get("database")
    or "factory_mes.db"
)

LANGUAGE = str(
    _CONFIG.get("language")
    or "vi"
)

THEME = str(
    _CONFIG.get("theme")
    or "light"
)
