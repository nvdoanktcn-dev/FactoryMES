from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
)

from src.database.base import Base


class CNCMachine(Base):
    """
    Danh mục máy CNC.

    Tách riêng khỏi Machine (danh mục máy chung) để module CNC
    có thể quản lý các thuộc tính đặc thù (số trục, hãng điều khiển...)
    mà không ảnh hưởng tới danh mục Machine hiện có.
    """

    __tablename__ = "tb_cnc_machine"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    machine_code = Column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )

    machine_name = Column(
        String(100),
        nullable=False,
    )

    machine_type = Column(
        String(30),
        nullable=True,
    )

    controller = Column(
        String(50),
        nullable=True,
    )

    axis_count = Column(
        Integer,
        nullable=True,
    )

    location = Column(
        String(100),
        nullable=True,
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
            f"<CNCMachine "
            f"code={self.machine_code!r} "
            f"name={self.machine_name!r}>"
        )
