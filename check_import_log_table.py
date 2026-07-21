from src.database.database import engine


with engine.connect() as connection:
    rows = connection.exec_driver_sql(
        "PRAGMA table_info(tb_import_log)"
    ).fetchall()

for row in rows:
    print(row)