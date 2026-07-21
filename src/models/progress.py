from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime

from src.database.base import Base


class Progress(Base):
    __tablename__ = "tb_progress"

    progress_id = Column(Integer, primary_key=True, autoincrement=True)

    work_order = Column(String(50), nullable=False)
    product_code = Column(String(30), nullable=False)

    plan_qty = Column(Integer, default=0)
    finished_qty = Column(Integer, default=0)
    remain_qty = Column(Integer, default=0)

    progress_percent = Column(Float, default=0)

    status = Column(String(20), default="OPEN")

    calculated_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Progress {self.work_order} {self.progress_percent}%>"