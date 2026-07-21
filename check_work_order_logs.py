from src.database.session import get_session
from src.models.production_log import ProductionLog


WORK_ORDER_NO = "WO202607001"

session = get_session()

try:
    logs = (
        session.query(ProductionLog)
        .filter(
            ProductionLog.work_order_no == WORK_ORDER_NO
        )
        .order_by(
            ProductionLog.op_no,
            ProductionLog.id,
        )
        .all()
    )

    if not logs:
        print(
            f"No Production Logs found for {WORK_ORDER_NO}."
        )
    else:
        print(
            f"Production Logs for {WORK_ORDER_NO}:"
        )

        for log in logs:
            print(
                f"Batch: {log.batch_no}"
                f" | OP: {log.op_no}"
                f" | Machine: {log.machine_code}"
                f" | OK: {log.ok_qty}"
                f" | NG: {log.ng_qty}"
            )

finally:
    session.close()