from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine


BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_PATH = BASE_DIR / "database" / "factory_mes.db"

DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={
        # Cho phép session được sử dụng trong các ngữ cảnh test/Qt khác nhau.
        "check_same_thread": False,

        # SQLite sẽ chờ khóa được giải phóng thay vì báo lỗi ngay.
        "timeout": 30,
    },
    pool_pre_ping=True,
)


@event.listens_for(Engine, "connect")
def configure_sqlite_connection(dbapi_connection, connection_record):
    """
    Cấu hình mỗi SQLite connection mới.

    WAL cho phép đọc và ghi đồng thời tốt hơn so với journal mặc định.
    busy_timeout giúp SQLite chờ khi một connection khác đang ghi.
    foreign_keys bảo đảm ràng buộc khóa ngoại được thực thi.
    """
    module_name = type(dbapi_connection).__module__

    if not module_name.startswith("sqlite3"):
        return

    cursor = dbapi_connection.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA busy_timeout = 30000")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
    finally:
        cursor.close()

@event.listens_for(engine, "checkout")
def debug_connection_checkout(
    dbapi_connection,
    connection_record,
    connection_proxy,
):
    del connection_record
    del connection_proxy

    print(
        "[DB CHECKOUT] "
        f"connection={id(dbapi_connection)}"
    )


@event.listens_for(engine, "checkin")
def debug_connection_checkin(
    dbapi_connection,
    connection_record,
):
    del connection_record

    print(
        "[DB CHECKIN ] "
        f"connection={id(dbapi_connection)}"
    )


@event.listens_for(engine, "begin")
def debug_transaction_begin(
    connection,
):
    print(
        "[TX BEGIN   ] "
        f"connection={id(connection.connection)}"
    )


@event.listens_for(engine, "commit")
def debug_transaction_commit(
    connection,
):
    print(
        "[TX COMMIT  ] "
        f"connection={id(connection.connection)}"
    )


@event.listens_for(engine, "rollback")
def debug_transaction_rollback(
    connection,
):
    print(
        "[TX ROLLBACK] "
        f"connection={id(connection.connection)}"
    )