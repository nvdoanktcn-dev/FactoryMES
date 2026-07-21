from sqlalchemy import Column, Integer, String, Date

from src.database.base import Base


class WorkOrder(Base):
    __tablename__ = "tb_work_order"

    id = Column(Integer, primary_key=True)

    work_order_no = Column(String(50), unique=True, nullable=False)
    product_code = Column(String(50), nullable=False)

    plan_qty = Column(Integer, default=0)

    start_date = Column(Date)
    due_date = Column(Date)

    status = Column(String(30), default="PLANNED")
    priority = Column(String(20), default="NORMAL")
    customer = Column(String(100))

    remark = Column(String(255))