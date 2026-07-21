from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)

from src.database.base import Base


class ImportLog(Base):
    __tablename__ = "tb_import_log"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    import_time = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        index=True,
    )

    module = Column(
        String(50),
        nullable=False,
        index=True,
    )

    file_name = Column(
        String(255),
        nullable=False,
    )

    sheet_name = Column(
        String(255),
        nullable=True,
    )

    user_name = Column(
        String(100),
        nullable=True,
    )

    total_rows = Column(
        Integer,
        nullable=False,
        default=0,
    )

    inserted_rows = Column(
        Integer,
        nullable=False,
        default=0,
    )

    updated_rows = Column(
        Integer,
        nullable=False,
        default=0,
    )

    failed_rows = Column(
        Integer,
        nullable=False,
        default=0,
    )

    duration = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    status = Column(
        String(30),
        nullable=False,
        default="SUCCESS",
        index=True,
    )

    message = Column(
        Text,
        nullable=True,
    )

    def __repr__(self):
        return (
            f"<ImportLog id={self.id} "
            f"module={self.module} "
            f"status={self.status}>"
        )