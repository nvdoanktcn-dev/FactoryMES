from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime

from src.database.base import Base


class MachineDowntime(Base):
    __tablename__ = "tb_machine_downtime"

    downtime_id = Column(Integer, primary_key=True, autoincrement=True)

    production_date = Column(Date, nullable=False)
    shift = Column(String(20), nullable=False)  # DAY / NIGHT

    machine_id = Column(String(20), nullable=False)

    reason_code = Column(String(20), nullable=False)  # DT01, DT02...

    downtime_min = Column(Float, default=0)

    source = Column(String(20))  # CNC / ROBOT

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return (
            f"<MachineDowntime {self.production_date} "
            f"{self.machine_id} {self.reason_code}>"
        )