from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.database.base import Base


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