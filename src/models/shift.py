from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime

from src.database.base import Base


class Shift(Base):
    __tablename__ = "tb_shift"

    shift_code = Column(String(20), primary_key=True)   # DAY / NIGHT

    shift_name_vi = Column(String(100), nullable=False)
    shift_name_cn = Column(String(100))

    start_time = Column(String(10), nullable=False)     # 08:00
    end_time = Column(String(10), nullable=False)       # 20:00

    available_min = Column(Integer, default=650)

    status = Column(String(20), default="ACTIVE")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Shift {self.shift_code}>"