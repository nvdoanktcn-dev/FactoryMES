from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from src.database.base import Base


class ProductionExecution(Base):
    __tablename__ = "tb_production_execution"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    assignment_id = Column(
        Integer,
        ForeignKey(
            "tb_production_assignment.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    start_time = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    end_time = Column(
        DateTime,
        nullable=True,
        index=True,
    )

    ok_qty = Column(
        Integer,
        nullable=False,
        default=0,
    )

    ng_qty = Column(
        Integer,
        nullable=False,
        default=0,
    )

    processing_ng_qty = Column(
        Integer,
        nullable=False,
        default=0,
    )

    blank_ng_qty = Column(
        Integer,
        nullable=False,
        default=0,
    )

    runtime_minutes = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    downtime_minutes = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    status = Column(
        String(30),
        nullable=False,
        default="RUNNING",
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