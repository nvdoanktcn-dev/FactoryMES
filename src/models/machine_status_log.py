from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from src.database.base import Base


class MachineStatusLog(Base):
    """Lịch sử thay đổi trạng thái của Machine."""

    __tablename__ = "tb_machine_status_log"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    machine_id = Column(
        Integer,
        ForeignKey(
            "tb_machine.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    machine_code = Column(
        String(30),
        nullable=False,
        index=True,
    )

    old_status = Column(
        String(30),
        nullable=True,
    )

    new_status = Column(
        String(30),
        nullable=False,
        index=True,
    )

    source = Column(
        String(50),
        nullable=False,
        default="MACHINE_CRUD",
        index=True,
    )

    changed_by = Column(
        String(100),
        nullable=True,
    )

    remark = Column(
        Text,
        nullable=True,
    )

    changed_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        index=True,
    )

    def __repr__(self):
        return (
            f"<MachineStatusLog id={self.id} "
            f"machine_code={self.machine_code} "
            f"old_status={self.old_status} "
            f"new_status={self.new_status}>"
        )
