from src.repository.base_repository import BaseRepository
from src.models.routing_snapshot import RoutingSnapshot


class RoutingSnapshotRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session, RoutingSnapshot)

    def get_by_work_order(self, work_order_no):
        return (
            self.session.query(RoutingSnapshot)
            .filter(RoutingSnapshot.work_order_no == work_order_no)
            .order_by(RoutingSnapshot.sequence)
            .all()
        )

    def delete_by_work_order(self, work_order_no):
        snapshots = self.get_by_work_order(work_order_no)

        for item in snapshots:
            self.session.delete(item)

        self.session.commit()