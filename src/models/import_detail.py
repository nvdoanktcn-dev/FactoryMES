from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from src.database.base import Base


class ImportDetail(Base):
    """
    Chi tiết từng bản ghi trong một lần Master Import.

    action:
        INSERT
        UPDATE
        DELETE
    """

    __tablename__ = "tb_import_detail"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    log_id = Column(
        Integer,
        ForeignKey(
            "tb_import_log.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    module = Column(
        String(50),
        nullable=False,
        index=True,
    )

    action = Column(
        String(20),
        nullable=False,
        index=True,
    )

    entity_key = Column(
        String(255),
        nullable=False,
        index=True,
    )

    old_json = Column(
        Text,
        nullable=True,
    )

    new_json = Column(
        Text,
        nullable=True,
    )

    created_time = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        index=True,
    )

    def __repr__(self):
        return (
            f"<ImportDetail id={self.id} "
            f"log_id={self.log_id} "
            f"action={self.action} "
            f"entity_key={self.entity_key}>"
        )