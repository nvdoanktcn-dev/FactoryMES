from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from src.database.base import Base


class ProductionAssignmentHistory(Base):
    __tablename__ = "tb_production_assignment_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, nullable=False, index=True)
    production_order_id = Column(Integer, nullable=False, index=True)
    action = Column(String(30), nullable=False, index=True)
    old_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=True)
    old_machine_code = Column(String(50), nullable=True)
    new_machine_code = Column(String(50), nullable=True)
    old_employee_code = Column(String(50), nullable=True)
    new_employee_code = Column(String(50), nullable=True)
    old_shift = Column(String(30), nullable=True)
    new_shift = Column(String(30), nullable=True)
    old_data_json = Column(Text, nullable=True)
    new_data_json = Column(Text, nullable=True)
    changed_by = Column(String(100), nullable=False, default="FactoryMES User")
    changed_at = Column(DateTime, nullable=False, default=datetime.now, index=True)
    remark = Column(String(255), nullable=True)
