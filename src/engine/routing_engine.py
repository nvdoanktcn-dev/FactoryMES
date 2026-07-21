from src.database.session import get_session
from src.framework.exception import NotFoundError, ValidationError

from src.repository.work_order_repository import WorkOrderRepository
from src.repository.routing_repository import RoutingRepository
from src.repository.routing_snapshot_repository import RoutingSnapshotRepository

from src.models.routing_snapshot import RoutingSnapshot


class RoutingEngine:
    def __init__(self):
        self.session = get_session()

        self.work_order_repository = WorkOrderRepository(self.session)
        self.routing_repository = RoutingRepository(self.session)
        self.snapshot_repository = RoutingSnapshotRepository(self.session)

    def create_snapshot(self, work_order_no):
        work_order_no = str(work_order_no).strip().upper()

        work_order = self.work_order_repository.get_by_no(work_order_no)

        if work_order is None:
            raise NotFoundError(f"Work Order not found: {work_order_no}")

        product_code = work_order.product_code

        routings = self.routing_repository.get_by_product(product_code)

        active_routings = [
            r for r in routings
            if (r.status or "").upper() == "ACTIVE"
        ]

        if not active_routings:
            raise ValidationError(
                f"No active routing found for product: {product_code}"
            )

        # Nếu đã có snapshot thì xóa và tạo lại.
        # Sau này khi WO đã RUNNING thì sẽ không cho tạo lại.
        self.snapshot_repository.delete_by_work_order(work_order_no)

        snapshots = []

        for routing in active_routings:
            snapshot = RoutingSnapshot(
                work_order_no=work_order_no,
                product_code=product_code,
                sequence=routing.sequence,
                op_no=routing.op_no,
                op_name=routing.op_name,
                process_type=routing.process_type,
                machine_type=routing.machine_type,
                machine_code=routing.machine_code,
                cycle_time_sec=routing.cycle_time_sec,
                setup_time_min=routing.setup_time_min,
                standard_output_hour=routing.standard_output_hour,
                status="READY",
                remark=routing.remark,
            )

            self.session.add(snapshot)
            snapshots.append(snapshot)

        self.session.commit()

        return snapshots

    def release_work_order(self, work_order_no):
         """
         Release Work Order

         1. Create Routing Snapshot
         2. Update Work Order Status
         """

         snapshots = self.create_snapshot(work_order_no)

         work_order = self.work_order_repository.get_by_no(work_order_no)

         work_order.status = "RELEASED"

         self.session.commit()

         return snapshots

    def release_work_order(self, work_order_no):
         snapshots = self.create_snapshot(work_order_no)

         work_order = self.work_order_repository.get_by_no(work_order_no)
         work_order.status = "RELEASED"

         self.session.commit()

         return snapshots         