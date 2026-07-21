from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

from src.database.base import Base


class PlanHistory(Base):
    __tablename__ = "tb_plan_history"

    history_id = Column(Integer, primary_key=True, autoincrement=True)

    work_order = Column(String(50), nullable=False)

    old_qty = Column(Integer, default=0)
    new_qty = Column(Integer, nullable=False)

    change_date = Column(DateTime, default=datetime.now)

    remark = Column(String(500))

    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<PlanHistory {self.work_order}: {self.old_qty}->{self.new_qty}>"