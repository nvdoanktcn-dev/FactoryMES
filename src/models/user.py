from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
)

from src.database.base import Base


class User(Base):
    __tablename__ = "tb_user"

    user_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    username = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )
    display_name = Column(
        String(100),
        nullable=False,
        default="",
    )
    password_hash = Column(
        String(512),
        nullable=False,
    )
    role = Column(
        String(30),
        nullable=False,
        default="VIEWER",
        index=True,
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )

    def __repr__(self) -> str:
        return (
            f"<User {self.username} "
            f"role={self.role} active={self.is_active}>"
        )
