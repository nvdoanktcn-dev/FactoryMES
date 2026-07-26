from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.database.base import Base
import src.models


BASE_DIR = Path(__file__).resolve().parents[2]
TEST_DATABASE_PATH = BASE_DIR / "test_factory_mes.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DATABASE_PATH}"


engine = create_engine(
    TEST_DATABASE_URL,
    future=True,
    echo=False,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
    },
    poolclass=NullPool,
)


TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def import_all_models() -> None:
    """
    Import every model module before create_all().

    SQLAlchemy only adds a mapped table to Base.metadata after the
    module declaring that model has been imported. Discovering the
    modules here also keeps the test schema synchronized when a new
    model is added later.
    """
    model_prefix = f"{src.models.__name__}."

    for module_info in pkgutil.walk_packages(
        src.models.__path__,
        prefix=model_prefix,
    ):
        importlib.import_module(module_info.name)


@event.listens_for(engine, "connect")
def configure_test_sqlite_connection(
    dbapi_connection,
    connection_record,
):
    cursor = dbapi_connection.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA busy_timeout = 30000")

        # Test suite chạy tuần tự và thường xuyên create/drop schema.
        # DELETE phù hợp hơn WAL cho database test dạng file.
        cursor.execute("PRAGMA journal_mode = DELETE")
        cursor.execute("PRAGMA synchronous = FULL")
    finally:
        cursor.close()

def create_test_database() -> None:
    engine.dispose()

    import_all_models()

    Base.metadata.create_all(
        bind=engine
    )


def drop_test_database() -> None:
    engine.dispose()

    try:
        Base.metadata.drop_all(
            bind=engine
        )
    finally:
        engine.dispose()

        for path in (
            TEST_DATABASE_PATH,
            Path(f"{TEST_DATABASE_PATH}-wal"),
            Path(f"{TEST_DATABASE_PATH}-shm"),
        ):
            try:
                path.unlink(missing_ok=True)
            except PermissionError:
                # Tránh che mất kết quả test nếu Windows vẫn đang
                # giải phóng file SQLite trong một khoảng rất ngắn.
                pass
