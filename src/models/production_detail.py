from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime

from src.database.base import Base


class ProductionDetail(Base):
    __tablename__ = "tb_production_detail"

    production_id = Column(Integer, primary_key=True, autoincrement=True)

    production_date = Column(Date, nullable=False)
    shift = Column(String(20), nullable=False)  # DAY / NIGHT

    machine_id = Column(String(20), nullable=False)
    employee_id = Column(String(20))

    work_order = Column(String(50), nullable=False)
    product_code = Column(String(30), nullable=False)

    operation_no = Column(String(20), nullable=False)

    runtime_min = Column(Float, default=0)

    ok_qty = Column(Integer, default=0)

    casting_ng_qty = Column(Integer, default=0)      # NG đúc / phôi NG
    machining_ng_qty = Column(Integer, default=0)    # NG gia công
    total_ng_qty = Column(Integer, default=0)

    source = Column(String(20))  # CNC / ROBOT

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return (
            f"<ProductionDetail {self.production_date} "
            f"{self.machine_id} {self.work_order} {self.operation_no}>"
        )