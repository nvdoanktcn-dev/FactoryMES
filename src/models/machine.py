from sqlalchemy import Column, Integer, String

from src.database.base import Base


class Machine(Base):
    __tablename__ = "tb_machine"

    id = Column(Integer, primary_key=True, autoincrement=True)

    machine_code = Column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )

    machine_name = Column(
        String(100),
        nullable=False,
    )

    machine_type = Column(String(30))
    line = Column(String(50))
    location = Column(String(100))
    brand = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100))
    status = Column(String(30), default="RUNNING")