from src.database.session import get_session
from src.models.routing_snapshot import RoutingSnapshot


WORK_ORDER_NO = "WO202607001"

session = get_session()

try:
    snapshots = (
        session.query(RoutingSnapshot)
        .filter(
            RoutingSnapshot.work_order_no == WORK_ORDER_NO
        )
        .order_by(RoutingSnapshot.sequence)
        .all()
    )

    if not snapshots:
        print(
            f"No Routing Snapshot found for {WORK_ORDER_NO}."
        )
    else:
        print(
            f"Routing Snapshot for {WORK_ORDER_NO}:"
        )

        for snapshot in snapshots:
            print(
                f"Sequence: {snapshot.sequence}"
                f" | OP: {snapshot.op_no}"
                f" | Machine: {snapshot.machine_code}"
                f" | Status: {snapshot.status}"
            )

finally:
    session.close()