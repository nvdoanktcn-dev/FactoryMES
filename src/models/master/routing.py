from sqlalchemy import Column, Integer, Float, String

from src.database.database import Base


class Routing(Base):
    __tablename__ = "tb_routing"

    routing_id = Column(Integer, primary_key=True, autoincrement=True)

    product_code = Column(String(30), nullable=False)

    operation_no = Column(String(20), nullable=False)

    sequence = Column(Integer, nullable=False)

    machine_group = Column(String(20), nullable=False)

    cycle_time_sec = Column(Float, nullable=False)

    is_last_operation = Column(Integer, default=0)