from src.database.database import engine


with engine.connect() as connection:
    columns = connection.exec_driver_sql(
        "PRAGMA table_info(tb_production_batch)"
    ).fetchall()


print("=" * 70)
print("tb_production_batch")
print("=" * 70)

if not columns:
    print("Table does not exist.")
else:
    for column in columns:
        print(column)