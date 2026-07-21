from src.database.session import get_session
from src.services.production_order_service import (
    ProductionOrderService,
)


session = get_session()

try:
    service = ProductionOrderService(
        session=session
    )

    production_order = (
        service.create_production_order(
            {
                "work_order_no": "TEST-WO-001",
                "product_code": "P001",
                "operation_no": "OP10",
                "operation_name": "CNC Turning",
                "process_type": "CNC",
                "machine_type": "CNC",
                "machine_code": "BL01",
                "employee_code": "E001",
                "shift": "DAY",
                "plan_qty": 1000,
                "completed_qty": 0,
                "ng_qty": 0,
                "status": "PLANNED",
                "planned_start": "2026-07-20 08:00",
                "planned_finish": "2026-07-20 20:00",
                "remark": "Transaction test",
            }
        )
    )

    print(
        production_order.work_order_no,
        production_order.operation_no,
        production_order.status,
    )

    assert production_order.work_order_no == (
        "TEST-WO-001"
    )

    assert production_order.operation_no == 10
    assert production_order.status == "PLANNED"

    session.rollback()

    print(
        "ProductionOrderService transaction test passed."
    )

finally:
    session.close()