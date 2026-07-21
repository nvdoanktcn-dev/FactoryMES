from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime

from src.database.base import Base


class FinishedInventory(Base):
    __tablename__ = "tb_finished_inventory"

    inventory_id = Column(Integer, primary_key=True, autoincrement=True)

    inventory_date = Column(Date, nullable=False)

    work_order = Column(String(50), nullable=False)
    product_code = Column(String(30), nullable=False)

    qty = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<FinishedInventory {self.work_order} {self.qty}>"