from sqlalchemy import Column, Integer, String, Float

from src.database.base import Base


class RoutingSnapshot(Base):
    __tablename__ = "tb_routing_snapshot"

    id = Column(Integer, primary_key=True)

    work_order_no = Column(String(50), nullable=False, index=True)

    product_code = Column(String(50), nullable=False)

    sequence = Column(Integer)

    op_no = Column(String(20))

    op_name = Column(String(100))

    process_type = Column(String(50))

    machine_type = Column(String(30))

    machine_code = Column(String(50))

    cycle_time_sec = Column(Float)

    setup_time_min = Column(Float)

    standard_output_hour = Column(Float)

    status = Column(String(20), default="READY")

    remark = Column(String(255))