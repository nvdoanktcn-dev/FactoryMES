from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime

from src.database.base import Base


class TechnicalItem(Base):
    __tablename__ = "tb_technical_item"

    item_code = Column(String(30), primary_key=True)

    item_name_vi = Column(String(200), nullable=False)
    item_name_cn = Column(String(200))

    category = Column(String(100))
    specification = Column(String(200))
    unit = Column(String(20))

    min_stock = Column(Integer, default=0)
    max_stock = Column(Integer, default=0)

    status = Column(String(20), default="ACTIVE")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<TechnicalItem {self.item_code}>"