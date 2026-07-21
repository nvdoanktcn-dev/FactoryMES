from sqlalchemy import Column, String

from src.database.database import Base


class Machine(Base):
    __tablename__ = "tb_machine"

    machine_id = Column(String(20), primary_key=True)

    machine_name = Column(String(100), nullable=False)

    machine_family = Column(String(20), nullable=False)

    machine_type = Column(String(20), nullable=False)

    machine_group = Column(String(20), nullable=False)

    status = Column(String(20), default="ACTIVE")