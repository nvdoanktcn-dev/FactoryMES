from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
)

from src.database.base import Base


class CNCProductionLog(Base):
    """
    Log sản xuất CNC được nạp từ file Excel/CSV (CNCImporter).

    Mỗi dòng dữ liệu hợp lệ trong file import tương ứng với
    một bản ghi CNCProductionLog. Tên cột tiếng Việt trong file
    gốc được DataCleaner/DataValidator chuẩn hóa trước khi
    CNCImporter.save() ánh xạ vào các trường bên dưới.
    """

    __tablename__ = "tb_cnc_production_log"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    log_date = Column(
        Date,
        nullable=True,
        index=True,
    )

    machine_name = Column(
        String(100),
        nullable=False,
        index=True,
    )

    work_order_no = Column(
        String(50),
        nullable=False,
        index=True,
    )

    product_name = Column(
        String(150),
        nullable=True,
    )

    operator_name = Column(
        String(100),
        nullable=True,
    )

    operation = Column(
        String(30),
        nullable=True,
    )

    shift = Column(
        String(20),
        nullable=True,
    )

    actual_time_hours = Column(
        Float,
        default=0,
    )

    qty_ok = Column(
        Float,
        default=0,
    )

    qty_ok_plus_ng = Column(
        Float,
        default=0,
    )

    total_ng = Column(
        Float,
        default=0,
    )

    raw_ng = Column(
        Float,
        default=0,
    )

    process_ng = Column(
        Float,
        default=0,
    )

    actual_pcs = Column(
        Float,
        default=0,
    )

    standard_pcs = Column(
        Float,
        default=0,
    )

    diff_pcs = Column(
        Float,
        default=0,
    )

    source_file = Column(
        String(255),
        nullable=True,
    )

    imported_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
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

    def __repr__(self):
        return (
            f"<CNCProductionLog "
            f"machine={self.machine_name!r} "
            f"wo={self.work_order_no!r}>"
        )
