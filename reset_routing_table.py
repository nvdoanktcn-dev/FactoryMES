from src.database.database import engine
from src.database.base import Base
import src.models

with engine.connect() as conn:
    conn.exec_driver_sql("DROP TABLE IF EXISTS tb_routing")
    conn.commit()

Base.metadata.create_all(bind=engine)

print("tb_routing recreated successfully.")