from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
)

from src.database.base import Base


class RobotOperationLog(Base):
    """
    Log vận hành Robot.

    Ghi nhận thời gian chạy, sản lượng và lỗi phát sinh của một
    robot theo ca/ngày. Nhập thủ công qua RobotOperationLogPage
    (chưa có importer Excel, khác với CNCProductionLog).
    """

    __tablename__ = "tb_robot_operation_log"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    robot_code = Column(
        String(30),
        nullable=False,
        index=True,
    )

    log_date = Column(
        Date,
        nullable=True,
        index=True,
    )

    shift = Column(
        String(20),
        nullable=True,
    )

    start_time = Column(
        DateTime,
        nullable=True,
    )

    end_time = Column(
        DateTime,
        nullable=True,
    )

    output_qty = Column(
        Float,
        default=0,
    )

    ng_qty = Column(
        Float,
        default=0,
    )

    error_code = Column(
        String(50),
        nullable=True,
    )

    error_message = Column(
        String(255),
        nullable=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="COMPLETED",
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
            f"<RobotOperationLog "
            f"robot={self.robot_code!r} "
            f"date={self.log_date!r}>"
        )
