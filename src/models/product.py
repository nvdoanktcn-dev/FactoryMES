from sqlalchemy import Column, String, DateTime
from datetime import datetime

from src.database.base import Base


class Product(Base):
    __tablename__ = "tb_product"

    product_code = Column(String(30), primary_key=True)
    product_name_vi = Column(String(200), nullable=False)
    product_name_cn = Column(String(200))
    customer = Column(String(100))
    material = Column(String(100))
    unit = Column(String(20), default="PCS")
    status = Column(String(20), default="ACTIVE")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    @property
    def product_name(self):
        return self.product_name_vi

    @product_name.setter
    def product_name(self, value):
        self.product_name_vi = value

    def __repr__(self):
        return f"<Product {self.product_code}>"