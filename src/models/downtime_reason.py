from datetime import datetime
from sqlalchemy import Column, String, DateTime

from src.database.base import Base


class DowntimeReason(Base):
    __tablename__ = "tb_downtime_reason"

    reason_code = Column(String(20), primary_key=True)

    reason_name_vi = Column(String(100), nullable=False)
    reason_name_cn = Column(String(100))

    category = Column(String(50))
    status = Column(String(20), default="ACTIVE")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<DowntimeReason {self.reason_code}>"