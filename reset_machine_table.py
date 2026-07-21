from src.database.base import Base
from src.database.database import engine

import src.models


def reset_machine_table():
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "DROP TABLE IF EXISTS tb_machine"
        )

    Base.metadata.create_all(bind=engine)

    print("tb_machine recreated successfully.")


if __name__ == "__main__":
    reset_machine_table()