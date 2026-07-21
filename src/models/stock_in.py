from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime

from src.database.base import Base


class StockIn(Base):
    __tablename__ = "tb_stock_in"

    stock_in_id = Column(Integer, primary_key=True, autoincrement=True)

    stock_in_date = Column(Date, nullable=False)

    item_code = Column(String(30), nullable=False)
    qty = Column(Float, default=0)

    supplier = Column(String(100))
    remark = Column(String(500))

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<StockIn {self.item_code} {self.qty}>"