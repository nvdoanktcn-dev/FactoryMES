from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
)

from src.database.base import Base


class Routing(Base):
    __tablename__ = "tb_routing"

    __table_args__ = (
        UniqueConstraint(
            "product_code",
            "operation_no",
            name="uq_routing_product_operation",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
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

    standard_cycle_time_sec = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    standard_output_pcs_hour = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    standard_operator_count = Column(
        Float,
        nullable=False,
        default=1.0,
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
            "<Routing "
            f"product={self.product_code!r} "
            f"operation={self.operation_no!r}>"
        )