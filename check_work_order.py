from src.database.session import get_session
from src.models.work_order import WorkOrder

session = get_session()

work_orders = session.query(WorkOrder).all()

print(f"Tổng số Work Order: {len(work_orders)}")

for wo in work_orders:
    print(
        wo.work_order,
        wo.product_code,
        wo.plan_qty,
        wo.status
    )