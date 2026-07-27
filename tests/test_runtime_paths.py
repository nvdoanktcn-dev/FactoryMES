from __future__ import annotations

from pathlib import Path

import src.models
from src.database.base import Base
from src.models.cnc_machine import CNCMachine
from src.models.cnc_production_log import CNCProductionLog
from src.models.robot import Robot
from src.models.robot_operation_log import RobotOperationLog
from src.utils import paths


def test_source_config_path_points_to_tracked_config() -> None:
    expected_path = (
        paths.project_root()
        / "config"
        / "app.json"
    )

    assert paths.config_path() == expected_path
    assert expected_path.is_file()


def test_source_icon_path_points_to_tracked_asset() -> None:
    expected_path = (
        paths.project_root()
        / "assets"
        / "factorymes_icon.png"
    )

    assert (
        paths.asset_path(
            "factorymes_icon.png"
        )
        == expected_path
    )
    assert expected_path.is_file()


def test_database_path_preserves_source_location(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        paths.DATA_DIRECTORY_ENV,
        raising=False,
    )

    assert paths.database_path() == (
        paths.project_root()
        / "database"
        / "factory_mes.db"
    )


def test_database_path_honors_data_directory_override(
    monkeypatch,
    tmp_path: Path,
) -> None:
    data_directory = (
        tmp_path
        / "FactoryMESData"
    )

    monkeypatch.setenv(
        paths.DATA_DIRECTORY_ENV,
        str(data_directory),
    )

    assert paths.database_path() == (
        data_directory
        / "database"
        / "factory_mes.db"
    )


def test_all_equipment_models_are_registered_before_create_all() -> None:
    for model_class in (
        CNCMachine,
        CNCProductionLog,
        Robot,
        RobotOperationLog,
    ):
        assert (
            model_class.__table__.key
            in Base.metadata.tables
        )
