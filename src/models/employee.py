from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
)

from src.database.base import Base


class Employee(Base):
    __tablename__ = "tb_employee"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    employee_code = Column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )

    employee_name = Column(
        String(100),
        nullable=False,
    )

    department = Column(
        String(50),
        nullable=True,
        index=True,
    )

    position = Column(
        String(50),
        nullable=True,
    )

    shift = Column(
        String(30),
        nullable=True,
        index=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE",
        index=True,
    )

    remark = Column(
        String(255),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )

    def __repr__(self):
        return (
            f"<Employee "
            f"code={self.employee_code!r} "
            f"name={self.employee_name!r}>"
        )