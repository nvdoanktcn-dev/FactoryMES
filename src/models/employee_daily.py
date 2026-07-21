from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime

from src.database.base import Base


class EmployeeDaily(Base):
    __tablename__ = "tb_employee_daily"

    employee_daily_id = Column(Integer, primary_key=True, autoincrement=True)

    production_date = Column(Date, nullable=False)
    shift = Column(String(20))

    employee_id = Column(String(20), nullable=False)

    working_min = Column(Float, default=0)

    ok_qty = Column(Integer, default=0)
    total_ng_qty = Column(Integer, default=0)

    pcs_per_hour = Column(Float, default=0)
    ng_rate_percent = Column(Float, default=0)

    calculated_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<EmployeeDaily {self.production_date} {self.employee_id}>"