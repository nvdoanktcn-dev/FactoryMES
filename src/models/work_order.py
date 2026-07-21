from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Integer,
    String,
)

from src.database.base import Base


class WorkOrder(Base):
    __tablename__ = "tb_work_order"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    work_order_no = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    product_code = Column(
        String(50),
        nullable=False,
        index=True,
    )

    plan_qty = Column(
        Integer,
        nullable=False,
        default=0,
    )

    start_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    due_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    priority = Column(
        String(20),
        nullable=False,
        default="NORMAL",
        index=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="PLANNED",
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
            "<WorkOrder "
            f"no={self.work_order_no!r} "
            f"product={self.product_code!r} "
            f"qty={self.plan_qty!r}>"
        )