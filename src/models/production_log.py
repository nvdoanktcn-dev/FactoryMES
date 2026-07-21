from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
)

from src.database.base import Base


class ProductionLog(Base):
    __tablename__ = "tb_production_log"

    __table_args__ = (
        UniqueConstraint(
            "record_hash",
            name="uq_production_log_record_hash",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # Khóa chống trùng cho từng bản ghi sản xuất
    record_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    # Thông tin công lệnh và sản phẩm
    work_order_no = Column(
        String(50),
        nullable=False,
        index=True,
    )

    product_code = Column(
        String(50),
        nullable=False,
        index=True,
    )

    # Thông tin công đoạn
    op_no = Column(
        String(20),
        nullable=False,
        index=True,
    )

    # Máy và nhân viên
    machine_code = Column(
        String(50),
        nullable=False,
        index=True,
    )

    employee_code = Column(
        String(50),
        nullable=False,
        index=True,
    )

    shift = Column(
        String(20),
        nullable=False,
        default="",
        index=True,
    )

    # Thời gian sản xuất
    start_time = Column(
        DateTime,
        nullable=True,
        index=True,
    )

    finish_time = Column(
        DateTime,
        nullable=True,
    )

    run_time_sec = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    # Sản lượng
    ok_qty = Column(
        Integer,
        nullable=False,
        default=0,
    )

    ng_qty = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # Dừng máy
    downtime_min = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    downtime_reason = Column(
        String(100),
        nullable=True,
    )

    # Trạng thái và ghi chú
    status = Column(
        String(30),
        nullable=False,
        default="COMPLETED",
        index=True,
    )

    remark = Column(
        String(255),
        nullable=True,
    )

    def __repr__(self):
        return (
            "<ProductionLog("
            f"id={self.id}, "
            f"work_order_no='{self.work_order_no}', "
            f"product_code='{self.product_code}', "
            f"op_no='{self.op_no}', "
            f"machine_code='{self.machine_code}', "
            f"ok_qty={self.ok_qty}, "
            f"ng_qty={self.ng_qty}"
            ")>"
        )