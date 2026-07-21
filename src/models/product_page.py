from sqlalchemy import Column, Integer, String

from src.database.base import Base


class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, autoincrement=True)

    machine_code = Column(String(30), unique=True, nullable=False)
    machine_name = Column(String(100), nullable=False)

    machine_type = Column(String(30))
    line = Column(String(50))
    location = Column(String(100))

    brand = Column(String(50))
    model = Column(String(50))
    serial_number = Column(String(100))

    status = Column(String(20), default="RUNNING")

    def __repr__(self):
        return f"<Machine {self.machine_code}>"