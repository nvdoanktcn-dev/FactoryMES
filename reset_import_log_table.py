from src.database.base import Base
from src.database.database import engine

import src.models


def reset_import_log_table():
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "DROP TABLE IF EXISTS tb_import_log"
        )

    Base.metadata.create_all(bind=engine)

    print("tb_import_log recreated successfully.")


if __name__ == "__main__":
    reset_import_log_table()