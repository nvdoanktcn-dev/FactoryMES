from src.database.database import engine

with engine.connect() as connection:
    rows = connection.exec_driver_sql(
        "PRAGMA table_info(tb_production_log)"
    ).fetchall()

print("=" * 60)
print("tb_production_log")
print("=" * 60)

for row in rows:
    print(row)