from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

from src.database.base import Base


class ShiftBreak(Base):
    __tablename__ = "tb_shift_break"

    break_id = Column(Integer, primary_key=True, autoincrement=True)

    shift_code = Column(String(20), nullable=False)

    break_name_vi = Column(String(100))
    break_name_cn = Column(String(100))

    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)

    break_min = Column(Integer, default=0)

    status = Column(String(20), default="ACTIVE")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<ShiftBreak {self.shift_code} {self.start_time}-{self.end_time}>"