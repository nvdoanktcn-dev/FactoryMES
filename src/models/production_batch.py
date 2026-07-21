from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
)

from src.database.base import Base


class ProductionBatch(Base):
    """
    Đại diện cho một lần nhập dữ liệu sản xuất.

    Ví dụ:
        PB202607100001
        PB202607100002
    """

    __tablename__ = "tb_production_batch"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    batch_no = Column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )

    import_type = Column(
        String(20),
        nullable=False,
        index=True,
    )

    file_name = Column(
        String(255),
        nullable=False,
    )

    file_hash = Column(
        String(64),
        nullable=True,
        index=True,
    )

    total_rows = Column(
        Integer,
        nullable=False,
        default=0,
    )

    success_rows = Column(
        Integer,
        nullable=False,
        default=0,
    )

    failed_rows = Column(
        Integer,
        nullable=False,
        default=0,
    )

    status = Column(
        String(20),
        nullable=False,
        default="CREATED",
        index=True,
    )

    imported_by = Column(
        String(50),
        nullable=True,
        default="System",
    )

    imported_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        index=True,
    )

    completed_at = Column(
        DateTime,
        nullable=True,
    )

    remark = Column(
        String(255),
        nullable=True,
    )

    def __repr__(self):
        return (
            "<ProductionBatch("
            f"id={self.id}, "
            f"batch_no='{self.batch_no}', "
            f"import_type='{self.import_type}', "
            f"status='{self.status}', "
            f"success_rows={self.success_rows}, "
            f"failed_rows={self.failed_rows}"
            ")>"
        )