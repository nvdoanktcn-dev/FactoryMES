from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
)

from src.database.base import Base


class Alarm(Base):
    """
    Giai đoạn 7 (MES Real-time, 2026-07-28): Alarm gắn với một máy cụ
    thể. Trước phase này, "Alarm" trên Dashboard (`AlarmTable` -
    `src/ui/dashboard/tables/alarm_table.py` - và sheet "Alarms" trong
    Excel export) chỉ là UI dựng sẵn từ trước, luôn hiển thị rỗng vì
    không có bảng dữ liệu thật nào đứng phía sau (`response.alarms`
    luôn là `[]`). Đây là bảng dữ liệu thật đầu tiên cho khái niệm đó.

    Alarm được ghi nhận thủ công (giống cách ghi nhận NG) - không tự
    động sinh ra từ ProductionDowntime/MachineDowntime, để giữ phạm vi
    rõ ràng: Alarm là một sự kiện cần người vận hành chú ý và xử lý,
    Downtime là một khoảng thời gian dừng máy đã biết nguyên nhân.
    """

    __tablename__ = "tb_alarm"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    machine_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    machine_code = Column(
        String(30),
        nullable=False,
        index=True,
    )

    alarm_code = Column(
        String(50),
        nullable=False,
        index=True,
    )

    message = Column(
        String(255),
        nullable=False,
    )

    # INFO / WARNING / ERROR / CRITICAL - khớp đúng 4 giá trị mà
    # AlarmTable đã tô màu sẵn từ trước (xem alarm_table.py).
    severity = Column(
        String(20),
        nullable=False,
        default="WARNING",
        index=True,
    )

    # OPEN / ACKNOWLEDGED / RESOLVED
    status = Column(
        String(20),
        nullable=False,
        default="OPEN",
        index=True,
    )

    raised_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        index=True,
    )

    acknowledged_at = Column(
        DateTime,
        nullable=True,
    )

    acknowledged_by = Column(
        String(50),
        nullable=True,
    )

    resolved_at = Column(
        DateTime,
        nullable=True,
    )

    resolved_by = Column(
        String(50),
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
            f"<Alarm {self.machine_code} "
            f"{self.severity} {self.status}>"
        )
