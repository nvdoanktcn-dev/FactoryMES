from sqlalchemy import Column, String

from src.database.database import Base


class Employee(Base):
    __tablename__ = "tb_employee"

    employee_id = Column(String(20), primary_key=True)

    employee_name = Column(String(100), nullable=False)

    department = Column(String(50))

    status = Column(String(20), default="ACTIVE")