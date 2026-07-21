from src.database.session import get_session
from src.services.work_order_service import (
    WorkOrderService,
)


session = get_session()

try:
    service = WorkOrderService(
        session=session
    )

    work_order, action = (
        service.save_work_order(
            {
                "work_order_no": "TEST-WO-001",
                "product_code": "P001",
                "plan_qty": 1000,
                "start_date": "2026-07-16",
                "due_date": "2026-07-30",
                "priority": "HIGH",
                "status": "PLANNED",
                "remark": "Transaction test",
            }
        )
    )

    print(
        work_order.work_order_no,
        work_order.product_code,
        work_order.plan_qty,
        action,
    )

    assert work_order.work_order_no == (
        "TEST-WO-001"
    )

    assert work_order.product_code == "P001"
    assert work_order.plan_qty == 1000

    assert action in {
        "created",
        "updated",
    }

    session.rollback()

    print(
        "WorkOrderService transaction test passed."
    )

finally:
    session.close()