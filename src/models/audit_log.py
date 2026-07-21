from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from src.database.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)

    table_name = Column(String(50))

    record_id = Column(Integer)

    action = Column(String(20))

    old_value = Column(Text)

    new_value = Column(Text)

    username = Column(String(50))

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )