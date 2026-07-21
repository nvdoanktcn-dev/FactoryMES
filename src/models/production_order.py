from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)

from src.database.base import Base


class ProductionOrder(Base):
    __tablename__ = "tb_production_order"

    __table_args__ = (
        UniqueConstraint(
            "work_order_no",
            "operation_no",
            name="uq_production_order_work_order_operation",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    work_order_no = Column(
        String(50),
        nullable=False,
        index=True,
    )

    product_code = Column(
        String(50),
        nullable=False,
        index=True,
    )

    operation_no = Column(
        Integer,
        nullable=False,
        index=True,
    )

    operation_name = Column(
        String(100),
        nullable=False,
    )

    process_type = Column(
        String(30),
        nullable=False,
        index=True,
    )

    machine_type = Column(
        String(30),
        nullable=True,
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

    plan_qty = Column(
        Integer,
        nullable=False,
        default=0,
    )

    completed_qty = Column(
        Integer,
        nullable=False,
        default=0,
    )

    ng_qty = Column(
        Integer,
        nullable=False,
        default=0,
    )

    status = Column(
        String(30),
        nullable=False,
        default="PLANNED",
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
            "<ProductionOrder "
            f"work_order={self.work_order_no!r} "
            f"operation={self.operation_no!r} "
            f"status={self.status!r}>"
        )