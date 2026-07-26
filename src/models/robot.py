from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
)

from src.database.base import Base


class Robot(Base):
    """
    Danh mục Robot trong nhà máy.

    Tương tự Machine nhưng dành riêng cho robot (cấp phôi, hàn,
    lắp ráp tự động...). area/station cho biết robot được gắn
    với khu vực/công đoạn sản xuất nào.
    """

    __tablename__ = "tb_robot"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    robot_code = Column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )

    robot_name = Column(
        String(100),
        nullable=False,
    )

    robot_type = Column(
        String(50),
        nullable=True,
    )

    area = Column(
        String(100),
        nullable=True,
    )

    station = Column(
        String(50),
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
            f"<Robot "
            f"code={self.robot_code!r} "
            f"name={self.robot_name!r}>"
        )
