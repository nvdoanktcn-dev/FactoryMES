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


class ProductionDowntime(Base):
    __tablename__ = "tb_production_downtime"

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

    reason_code = Column(
        String(50),
        nullable=False,
        index=True,
    )

    reason_name = Column(
        String(150),
        nullable=False,
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

    duration_minutes = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    status = Column(
        String(30),
        nullable=False,
        default="OPEN",
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
            "<ProductionDowntime "
            f"id={self.id!r} "
            f"execution_id={self.execution_id!r} "
            f"reason={self.reason_code!r} "
            f"status={self.status!r}>"
        )