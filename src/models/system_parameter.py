from datetime import datetime
from sqlalchemy import Column, String, DateTime

from src.database.base import Base


class SystemParameter(Base):
    __tablename__ = "tb_system_parameter"

    parameter_code = Column(String(50), primary_key=True)

    parameter_value = Column(String(200))
    description = Column(String(500))

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<SystemParameter {self.parameter_code}>"