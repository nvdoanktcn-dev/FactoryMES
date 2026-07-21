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


class ProductionNG(Base):
    __tablename__ = "tb_production_ng"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    execution_id = Column(
        Integer,
        ForeignKey(
            "tb_production_execution.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    ng_type = Column(
        String(30),
        nullable=False,
        index=True,
    )

    reason_code = Column(
        String(50),
        nullable=False,
        index=True,
    )

    reason_name = Column(
        String(150),
        nullable=False,
    )

    quantity = Column(
        Integer,
        nullable=False,
        default=0,
    )

    recorded_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        index=True,
    )

    employee_code = Column(
        String(50),
        nullable=True,
        index=True,
    )

    remark = Column(
        String(255),
        nullable=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE",
        index=True,
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