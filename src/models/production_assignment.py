from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)

from src.database.base import Base


class ProductionAssignment(Base):
    __tablename__ = "tb_production_assignment"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    production_order_id = Column(
        Integer,
        ForeignKey(
            "tb_production_order.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    machine_code = Column(
        String(50),
        nullable=True,
        index=True,
    )

    employee_code = Column(
        String(50),
        nullable=True,
        index=True,
    )

    shift = Column(
        String(30),
        nullable=True,
        index=True,
    )

    planned_start = Column(
        DateTime,
        nullable=True,
        index=True,
    )

    planned_finish = Column(
        DateTime,
        nullable=True,
        index=True,
    )

    status = Column(
        String(30),
        nullable=False,
        default="DRAFT",
        index=True,
    )

    assigned_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    released_at = Column(
        DateTime,
        nullable=True,
    )

    actual_start = Column(
        DateTime,
        nullable=True,
    )

    actual_finish = Column(
        DateTime,
        nullable=True,
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
            "<ProductionAssignment "
            f"id={self.id!r} "
            f"production_order_id="
            f"{self.production_order_id!r} "
            f"machine={self.machine_code!r} "
            f"employee={self.employee_code!r}>"
        )