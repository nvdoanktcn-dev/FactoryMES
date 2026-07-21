from src.database.database import engine


with engine.connect() as connection:
    columns = connection.exec_driver_sql(
        "PRAGMA table_info(tb_machine)"
    ).fetchall()

print("=" * 70)
print("tb_machine")
print("=" * 70)

for column in columns:
    print(column)