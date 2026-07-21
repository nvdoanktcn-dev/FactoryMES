from src.database.session import get_session
from src.models.work_order import WorkOrder


session = get_session()

try:
    work_orders = (
        session.query(WorkOrder)
        .order_by(WorkOrder.id)
        .all()
    )

    if not work_orders:
        print("No Work Orders found.")
    else:
        print("Available Work Orders:")

        for work_order in work_orders:
            print(
                work_order.work_order_no,
                "| Product:",
                work_order.product_code,
                "| Status:",
                work_order.status,
            )

finally:
    session.close()